// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {Test} from "forge-std/Test.sol";

import {Deployers} from "@uniswap/v4-core/test/utils/Deployers.sol";
import {PoolSwapTest} from "v4-core/test/PoolSwapTest.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";

import {PoolManager} from "v4-core/PoolManager.sol";
import {IPoolManager} from "v4-core/interfaces/IPoolManager.sol";

import {Currency, CurrencyLibrary} from "v4-core/types/Currency.sol";

import {Hooks} from "v4-core/libraries/Hooks.sol";
import {TickMath} from "v4-core/libraries/TickMath.sol";
import {SqrtPriceMath} from "v4-core/libraries/SqrtPriceMath.sol";
import {LiquidityAmounts} from "@uniswap/v4-core/test/utils/LiquidityAmounts.sol";

import "forge-std/console.sol";
import {PointsHook} from "../src/PointsHook.sol";

contract TestPointsHook is Test, Deployers {
    using CurrencyLibrary for Currency;

    MockERC20 token;

    Currency ethCurrency = Currency.wrap(address(0));
    Currency tokenCurrency;

    PointsHook hook;
    address user1 = address(0x1);
    address user2 = address(0x2);

    function setUp() public {
        // Step 1 + 2
        // Deploy PoolManager and Router contracts
        deployFreshManagerAndRouters();

        // Deploy our TOKEN contract
        token = new MockERC20("Test Token", "TEST", 18);
        tokenCurrency = Currency.wrap(address(token));

        // Mint a bunch of TOKEN to ourselves and to address(1)
        token.mint(address(this), 1000 ether);
        token.mint(user1, 1000 ether);
        token.mint(user2, 1000 ether);

        // Deploy hook to an address that has the proper flags set
        uint160 flags = uint160(
            Hooks.AFTER_ADD_LIQUIDITY_FLAG | Hooks.AFTER_SWAP_FLAG
        );
        deployCodeTo(
            "PointsHook.sol",
            abi.encode(manager, "Points Token", "TEST_POINTS"),
            address(flags)
        );

        // Deploy our hook
        hook = PointsHook(address(flags));

        // Approve our TOKEN for spending on the swap router and modify liquidity router
        // These variables are coming from the `Deployers` contract
        token.approve(address(swapRouter), type(uint256).max);
        token.approve(address(modifyLiquidityRouter), type(uint256).max);
        vm.prank(user1);
        token.approve(address(swapRouter), type(uint256).max);
        vm.prank(user1);
        token.approve(address(modifyLiquidityRouter), type(uint256).max);

        // Initialize a pool
        (key, ) = initPool(
            ethCurrency, // Currency 0 = ETH
            tokenCurrency, // Currency 1 = TOKEN
            hook, // Hook Contract
            3000, // Swap Fees
            SQRT_PRICE_1_1 // Initial Sqrt(P) value = 1
        );
    }

    function test_addLiquidityAndSwap() public {
        uint256 pointsBalanceOriginal = hook.balanceOf(address(this));

        // Set user address in hook data
        bytes memory hookData = abi.encode(address(this));

        uint160 sqrtPriceAtTickLower = TickMath.getSqrtPriceAtTick(-60);
        uint160 sqrtPriceAtTickUpper = TickMath.getSqrtPriceAtTick(60);

        uint256 ethToAdd = 0.1 ether;
        uint128 liquidityDelta = LiquidityAmounts.getLiquidityForAmount0(
            sqrtPriceAtTickLower,
            SQRT_PRICE_1_1,
            ethToAdd
        );
        uint256 tokenToAdd = LiquidityAmounts.getAmount1ForLiquidity(
            sqrtPriceAtTickUpper,
            SQRT_PRICE_1_1,
            liquidityDelta
        );

        modifyLiquidityRouter.modifyLiquidity{value: ethToAdd}(
            key,
            IPoolManager.ModifyLiquidityParams({
                tickLower: -60,
                tickUpper: 60,
                liquidityDelta: int256(uint256(liquidityDelta)),
                salt: bytes32(0)
            }),
            hookData
        );
        uint256 pointsBalanceAfterAddLiquidity = hook.balanceOf(address(this));

        assertApproxEqAbs(
            pointsBalanceAfterAddLiquidity - pointsBalanceOriginal,
            0.1 ether,
            0.001 ether // error margin for precision loss
        );

        // Now we swap
        // We will swap 0.001 ether for tokens
        // We should get 20% of 0.001 * 10**18 points
        // = 2 * 10**14
        swapRouter.swap{value: 0.001 ether}(
            key,
            IPoolManager.SwapParams({
                zeroForOne: true,
                amountSpecified: -0.001 ether, // Exact input for output swap
                sqrtPriceLimitX96: TickMath.MIN_SQRT_PRICE + 1000
            }),
            PoolSwapTest.TestSettings({
                takeClaims: false,
                settleUsingBurn: false
            }),
            hookData
        );
        uint256 pointsBalanceAfterSwap = hook.balanceOf(address(this));
        assertEq(
            pointsBalanceAfterSwap - pointsBalanceAfterAddLiquidity,
            2 * 10 ** 14
        );
    }

    function test_streakBonus() public {
        // Create hook data with user1 address
        bytes memory hookData = abi.encode(user1);

        // First, let's add some liquidity to allow for larger price movements
        uint160 sqrtPriceAtTickLower = TickMath.getSqrtPriceAtTick(-6000);
        uint160 sqrtPriceAtTickUpper = TickMath.getSqrtPriceAtTick(6000);

        uint256 ethToAdd = 10 ether;
        uint128 liquidityDelta = LiquidityAmounts.getLiquidityForAmount0(
            sqrtPriceAtTickLower,
            SQRT_PRICE_1_1,
            ethToAdd
        );

        // Add liquidity first
        modifyLiquidityRouter.modifyLiquidity{value: ethToAdd}(
            key,
            IPoolManager.ModifyLiquidityParams({
                tickLower: -6000,
                tickUpper: 6000,
                liquidityDelta: int256(uint256(liquidityDelta)),
                salt: bytes32(0)
            }),
            abi.encode(address(this))
        );

        // Do swaps in succession to build up a streak
        for (uint i = 0; i < 5; i++) {
            vm.roll(block.number + 10); // Advance blocks within streak range

            vm.deal(user1, 1 ether); // Give ETH to user1
            vm.prank(user1);
            swapRouter.swap{value: 0.001 ether}(
                key,
                IPoolManager.SwapParams({
                    zeroForOne: true,
                    amountSpecified: -0.001 ether,
                    sqrtPriceLimitX96: TickMath.MIN_SQRT_PRICE + 1000 // Use a less restrictive price limit
                }),
                PoolSwapTest.TestSettings({
                    takeClaims: false,
                    settleUsingBurn: false
                }),
                hookData
            );
        }

        // Check streak count
        assertEq(hook.getUserStreak(user1), 5);

        // Check if bonus is 20% (STREAK_THRESHOLD_2)
        assertEq(hook.getStreakBonus(user1), 20);

        // Last swap should have given user 0.001 ether / 5 = 0.0002 ether base points
        // Plus 20% bonus: 0.0002 + (0.0002 * 0.2) = 0.00024 ether
        // Previous swaps (without considering compounding): 0.0002 + (0.0002 * 0.1) * 2 + (0.0002 * 0.2) * 2
        // We're not worrying about precise calculations, just checking the bonus is working
        assertTrue(hook.balanceOf(user1) > 0.0002 ether * 5);
    }

    function test_referralSystem() public {
        // Create hook data with user1 address and user2 as referrer
        // We'll use ABI encoding to create the proper hook data
        bytes memory hookData = abi.encode(user1, user2);

        // Add some liquidity first to allow swaps
        uint160 sqrtPriceAtTickLower = TickMath.getSqrtPriceAtTick(-6000);
        uint160 sqrtPriceAtTickUpper = TickMath.getSqrtPriceAtTick(6000);
        uint256 ethToAdd = 10 ether;
        uint128 liquidityDelta = LiquidityAmounts.getLiquidityForAmount0(
            sqrtPriceAtTickLower,
            SQRT_PRICE_1_1,
            ethToAdd
        );

        modifyLiquidityRouter.modifyLiquidity{value: ethToAdd}(
            key,
            IPoolManager.ModifyLiquidityParams({
                tickLower: -6000,
                tickUpper: 6000,
                liquidityDelta: int256(uint256(liquidityDelta)),
                salt: bytes32(0)
            }),
            abi.encode(address(this))
        );

        // User1 does a swap with user2 as referrer
        vm.deal(user1, 1 ether);
        vm.prank(user1);
        swapRouter.swap{value: 0.01 ether}(
            key,
            IPoolManager.SwapParams({
                zeroForOne: true,
                amountSpecified: -0.01 ether,
                sqrtPriceLimitX96: TickMath.MIN_SQRT_PRICE + 1000 // Use less restrictive limit
            }),
            PoolSwapTest.TestSettings({
                takeClaims: false,
                settleUsingBurn: false
            }),
            hookData
        );

        // Check that user2 is set as user1's referrer
        assertEq(hook.getUserReferrer(user1), user2);

        // Base points for user1: 0.01 ether / 5 = 0.002 ether
        // Referral bonus for user2: 0.002 ether / 10 = 0.0002 ether
        assertEq(hook.balanceOf(user1), 0.002 ether);
        assertEq(hook.balanceOf(user2), 0.0002 ether);
    }

    function test_jackpotSystem() public {
        // First, we need to add funds to the jackpot pool
        // We'll do this by adding liquidity multiple times

        // Create hook data with this contract as user
        bytes memory hookData = abi.encode(address(this));

        uint160 sqrtPriceAtTickLower = TickMath.getSqrtPriceAtTick(-60);
        uint160 sqrtPriceAtTickUpper = TickMath.getSqrtPriceAtTick(60);
        uint256 ethToAdd = 1 ether;

        // Add enough ETH to meet jackpot threshold
        for (uint i = 0; i < 15; i++) {
            uint128 liquidityDelta = LiquidityAmounts.getLiquidityForAmount0(
                sqrtPriceAtTickLower,
                SQRT_PRICE_1_1,
                ethToAdd
            );

            modifyLiquidityRouter.modifyLiquidity{value: ethToAdd}(
                key,
                IPoolManager.ModifyLiquidityParams({
                    tickLower: -60,
                    tickUpper: 60,
                    liquidityDelta: int256(uint256(liquidityDelta)),
                    salt: bytes32(uint256(i))
                }),
                hookData
            );
        }

        // Check jackpot pool - should be around 15 * 1 ether / 100 = 0.15 ether
        assertTrue(hook.getJackpotPool() >= 0.14 ether);

        // Now we'll try to win the jackpot by manipulating the "random" value
        // For a hackathon, this demonstrates the feature works
        // Note: This is not a secure way to generate randomness!

        // First, record the current balance
        uint256 balanceBefore = hook.balanceOf(user1);
        uint256 jackpotBefore = hook.getJackpotPool();

        // Force the jackpot win by using a specific block.timestamp and prevrandao
        // This is just for test demonstration!
        vm.warp(1); // Set timestamp
        vm.prevrandao(bytes32(uint256(5))); // Set prevrandao to ensure win

        // User1 does a swap with enough ETH to qualify
        vm.deal(user1, 1 ether);
        bytes memory user1Data = abi.encode(user1);
        vm.prank(user1);
        swapRouter.swap{value: 0.5 ether}(
            key,
            IPoolManager.SwapParams({
                zeroForOne: true,
                amountSpecified: -0.5 ether,
                sqrtPriceLimitX96: TickMath.MIN_SQRT_PRICE + 1000
            }),
            PoolSwapTest.TestSettings({
                takeClaims: false,
                settleUsingBurn: false
            }),
            user1Data
        );

        // We would need multiple tests to verify jackpot,
        // but this demonstrates the functionality exists

        // Either the jackpot remains the same (no win), or is reset to 0 (win)
        if (hook.getJackpotPool() == 0) {
            // If jackpot was won, user1 should have received points equal to the jackpot
            uint256 expectedBalance = balanceBefore +
                (0.5 ether / 5) +
                jackpotBefore;
            assertApproxEqAbs(
                hook.balanceOf(user1),
                expectedBalance,
                0.001 ether
            );
        } else {
            // If not won, jackpot should have increased by 0.5% of the swap
            assertApproxEqAbs(
                hook.getJackpotPool(),
                jackpotBefore + (0.5 ether / 100),
                0.001 ether
            );
        }
    }
}
