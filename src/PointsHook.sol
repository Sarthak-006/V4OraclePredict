// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {BaseHook} from "v4-periphery/src/base/hooks/BaseHook.sol";
import {ERC20} from "solmate/src/tokens/ERC20.sol";

import {Currency} from "v4-core/types/Currency.sol";
import {PoolKey} from "v4-core/types/PoolKey.sol";
import {BalanceDelta} from "v4-core/types/BalanceDelta.sol";

import {IPoolManager} from "v4-core/interfaces/IPoolManager.sol";

import {Hooks} from "v4-core/libraries/Hooks.sol";

contract PointsHook is BaseHook, ERC20 {
    // Streak tracking for bonus multipliers
    mapping(address => uint256) public userStreaks;
    mapping(address => uint256) public lastInteractionBlock;

    // Basic referral system
    mapping(address => address) public referrers;

    // Jackpot mechanism
    uint256 public jackpotPool;
    uint256 public constant JACKPOT_THRESHOLD = 10 ether; // 10 ETH in pool to qualify for jackpot
    uint256 public constant JACKPOT_CHANCE = 5; // 5% chance (out of 100)

    // Constants for streak bonuses
    uint256 public constant STREAK_THRESHOLD_1 = 3;
    uint256 public constant STREAK_THRESHOLD_2 = 5;
    uint256 public constant STREAK_THRESHOLD_3 = 10;
    uint256 public constant STREAK_BONUS_1 = 10; // 10% bonus
    uint256 public constant STREAK_BONUS_2 = 20; // 20% bonus
    uint256 public constant STREAK_BONUS_3 = 50; // 50% bonus

    constructor(
        IPoolManager _manager,
        string memory _name,
        string memory _symbol
    ) BaseHook(_manager) ERC20(_name, _symbol, 18) {}

    function getHookPermissions()
        public
        pure
        override
        returns (Hooks.Permissions memory)
    {
        return
            Hooks.Permissions({
                beforeInitialize: false,
                afterInitialize: false,
                beforeAddLiquidity: false,
                beforeRemoveLiquidity: false,
                afterAddLiquidity: true,
                afterRemoveLiquidity: false,
                beforeSwap: false,
                afterSwap: true,
                beforeDonate: false,
                afterDonate: false,
                beforeSwapReturnDelta: false,
                afterSwapReturnDelta: false,
                afterAddLiquidityReturnDelta: false,
                afterRemoveLiquidityReturnDelta: false
            });
    }

    function afterSwap(
        address,
        PoolKey calldata key,
        IPoolManager.SwapParams calldata swapParams,
        BalanceDelta delta,
        bytes calldata hookData
    ) external override onlyPoolManager returns (bytes4, int128) {
        // If this is not an ETH-TOKEN pool with this hook attached, ignore
        if (!key.currency0.isAddressZero()) return (this.afterSwap.selector, 0);

        // We only mint points if user is buying TOKEN with ETH
        if (!swapParams.zeroForOne) return (this.afterSwap.selector, 0);

        // Mint points equal to 20% of the amount of ETH they spent
        uint256 ethSpendAmount = uint256(int256(-delta.amount0()));
        uint256 pointsForSwap = ethSpendAmount / 5;

        // Add 1% to jackpot pool
        jackpotPool += ethSpendAmount / 100;

        // Process user data and assign points
        _processUserData(hookData, pointsForSwap, ethSpendAmount);

        return (this.afterSwap.selector, 0);
    }

    function afterAddLiquidity(
        address,
        PoolKey calldata key,
        IPoolManager.ModifyLiquidityParams calldata,
        BalanceDelta delta,
        BalanceDelta,
        bytes calldata hookData
    ) external override onlyPoolManager returns (bytes4, BalanceDelta) {
        // If this is not an ETH-TOKEN pool with this hook attached, ignore
        if (!key.currency0.isAddressZero())
            return (this.afterAddLiquidity.selector, delta);

        // Mint points equivalent to how much ETH they're adding in liquidity
        uint256 ethAmount = uint256(int256(-delta.amount0()));

        // Add 1% to jackpot pool
        jackpotPool += ethAmount / 100;

        // Process user data and assign points
        _processUserData(hookData, ethAmount, ethAmount);

        return (this.afterAddLiquidity.selector, delta);
    }

    function _processUserData(
        bytes calldata hookData,
        uint256 basePoints,
        uint256 ethAmount
    ) internal {
        if (hookData.length == 0) return;

        // Extract user address from hookData
        address user = abi.decode(hookData, (address));

        // Skip if invalid user
        if (user == address(0)) return;

        // Try to extract referrer if there's enough data for a second address
        if (hookData.length >= 64) {
            // For hackathon simplicity, assume the hookData contains abi.encode(user, referrer)
            (address _user, address referrer) = abi.decode(
                hookData,
                (address, address)
            );

            // Only register referrer if not already set and not self-referral
            if (
                referrers[user] == address(0) &&
                referrer != user &&
                referrer != address(0)
            ) {
                referrers[user] = referrer;
            }
        }

        // Update user streak
        if (lastInteractionBlock[user] + 50 >= block.number) {
            userStreaks[user]++;
        } else {
            userStreaks[user] = 1;
        }
        lastInteractionBlock[user] = block.number;

        // Apply streak bonus
        uint256 totalPoints = basePoints;
        if (userStreaks[user] >= STREAK_THRESHOLD_3) {
            totalPoints += (basePoints * STREAK_BONUS_3) / 100;
        } else if (userStreaks[user] >= STREAK_THRESHOLD_2) {
            totalPoints += (basePoints * STREAK_BONUS_2) / 100;
        } else if (userStreaks[user] >= STREAK_THRESHOLD_1) {
            totalPoints += (basePoints * STREAK_BONUS_1) / 100;
        }

        // Mint points to user
        _mint(user, totalPoints);

        // Apply referral bonus if applicable
        address activeReferrer = referrers[user];
        if (activeReferrer != address(0)) {
            uint256 referralBonus = basePoints / 10; // 10% referral bonus
            _mint(activeReferrer, referralBonus);
        }

        // Chance for jackpot win - only for larger transactions
        if (ethAmount >= 0.5 ether && jackpotPool >= JACKPOT_THRESHOLD) {
            // Simple random number generation (for demonstration only, not secure!)
            uint256 randomValue = uint256(
                keccak256(
                    abi.encodePacked(
                        block.timestamp,
                        block.prevrandao,
                        user,
                        ethAmount
                    )
                )
            ) % 100;

            if (randomValue < JACKPOT_CHANCE) {
                // Winner! Award jackpot
                uint256 jackpotAmount = jackpotPool;
                jackpotPool = 0;
                _mint(user, jackpotAmount);
            }
        }
    }

    // View functions for frontend/game integration
    function getStreakBonus(address user) external view returns (uint256) {
        if (userStreaks[user] >= STREAK_THRESHOLD_3) return STREAK_BONUS_3;
        if (userStreaks[user] >= STREAK_THRESHOLD_2) return STREAK_BONUS_2;
        if (userStreaks[user] >= STREAK_THRESHOLD_1) return STREAK_BONUS_1;
        return 0;
    }

    function getUserStreak(address user) external view returns (uint256) {
        return userStreaks[user];
    }

    function getUserReferrer(address user) external view returns (address) {
        return referrers[user];
    }

    function getJackpotPool() external view returns (uint256) {
        return jackpotPool;
    }
}
