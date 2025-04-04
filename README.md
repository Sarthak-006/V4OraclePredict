# V4 Oracle Predict

A gamified liquidity and trading experience built on Uniswap V4 hooks.

## Demo

- [Live Demo App](https://v4oraclepredict.streamlit.app/)
- [Demo Video](https://www.youtube.com/watch?v=kBrRu_DnVRQ)

## 📖 How to Play V4 Oracle Predict

Welcome! Predict outcomes based on simulated Oracle signals processed by a V4 Hook concept.

**The Process (Simulated):**
1.  **Feed 1:** Hook reads 3 Oracle values (e.g., `[2,5,8]`). Calculates **Pressure Signal** (sum%10 ➜ `5`).
2.  **Feed 2:** Hook reads 3 more values (e.g., `[3,6,9]`). Calculates **Momentum Signal** (sum%10 ➜ `8`).
3.  The **Combined Signal** is `Pressure` + `Momentum` (e.g., `58`).

**Prediction Types (Core Game Logic):**
*   **Signal Prediction (10.0x):** Predict the `Pressure` **OR** `Momentum` signal digit (0-9).
*   **Combined Signal (90.0x):** Predict the final two-digit combined signal (00-99).
*   **Unique Oracle Pattern (150.0x):** Predict a `XYZ` pattern (3 unique digits) in either Feed 1 **OR** Feed 2 raw data.
*   **Repeating Oracle Pattern (300.0x):** Predict a `XXY`/`XYY` pattern (2 same digits) in either Feed 1 **OR** Feed 2.
*   **Consensus Oracle Pattern (500.0x + Jackpot):** Predict a `XXX` pattern (3 same digits) in either Feed 1 **OR** Feed 2. Win gives Jackpot chance!

**Features:** Win Streaks (3/5/10 wins = +10%/+20%/+50% bonus) & Progressive V4 Jackpot.
**Disclaimer:** Simulation for entertainment. Not real financial advice. Play Responsibly.

## Overview

V4 Oracle Predict combines DeFi engagement with gamification by rewarding users with points for participating in Uniswap V4 pools. Users earn points for swapping ETH for tokens and for providing liquidity. The project introduces game mechanics like streak bonuses, referral incentives, and a jackpot system.

## Key Features

- **Points Reward System**: Earn points for swapping ETH for tokens (20% of ETH spent) and adding liquidity (1:1 with ETH added)
- **Streak Bonuses**: Consistent activity builds a streak with escalating bonuses:
  - 3+ consecutive interactions: 10% bonus
  - 5+ consecutive interactions: 20% bonus
  - 10+ consecutive interactions: 50% bonus
- **Referral System**: Earn 10% of the points generated by users you refer
- **Jackpot Mechanics**: Chance to win the accumulated jackpot pool when performing larger swaps

## Technical Implementation

### Smart Contract

The core of the project is the `PointsHook` contract which implements the Uniswap V4 hook interface. The hook:

1. Monitors pool events (swaps and liquidity additions)
2. Tracks user interaction streaks
3. Issues ERC20 tokens as points
4. Maintains a jackpot pool
5. Processes referrals

### How It Works

- **Hook Permissions**: The contract hooks into `afterAddLiquidity` and `afterSwap` events
- **Point Minting Logic**: Points are minted based on ETH liquidity added or ETH spent in swaps
- **Data Passing**: User addresses (and optional referrers) are passed via hook data
- **Jackpot Mechanism**: A percentage of all ETH volume contributes to the jackpot

## License

This project is licensed under the MIT License.

## Use Cases

- **Incentivizing Liquidity**: Pool creators can reward consistent liquidity providers
- **Gamified Trading**: Make trading more engaging and rewarding
- **Referral Growth**: Encourage users to invite friends via the referral program
- **Jackpot Excitement**: Large trades have a chance to win big rewards



## Acknowledgements

- Built using Uniswap V4 hooks framework
- Frontend simulator inspired by prediction markets
- Developed for educational and demonstration purposes 