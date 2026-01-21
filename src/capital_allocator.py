from typing import List, Dict, Optional
from enum import Enum


class AllocationStrategy(Enum):
    EQUAL = "equal"


PLATFORM_MIN_BET = 5.0


def equal_weight_allocation(opportunities: List[Dict], total_capital: float) -> List[Dict]:
    if not opportunities:
        return []

    allocation_per_opportunity = total_capital / len(opportunities)

    allocations = []
    for opp in opportunities:
        if allocation_per_opportunity >= PLATFORM_MIN_BET * 2:
            allocations.append({
                'opportunity': opp,
                'allocated_capital': allocation_per_opportunity
            })

    return allocations


def calculate_bet_amounts(opp: Dict, allocated_capital: float) -> Optional[Dict]:
    arb = opp['arbitrage']
    best = arb['best_strategy']

    if not best:
        return None

    strategy_type = best['type']

    if 'Yes on App1, No on App2' in strategy_type:
        price_yes = arb['market1_yes']
        price_no = arb['market2_no']
        platform_yes = "Polymarket"
        platform_no = "predict.fun"
    else:
        price_yes = arb['market2_yes']
        price_no = arb['market1_no']
        platform_yes = "predict.fun"
        platform_no = "Polymarket"

    total_price = price_yes + price_no
    if total_price == 0:
        return None

    bet_yes = allocated_capital * (price_yes / total_price)
    bet_no = allocated_capital * (price_no / total_price)

    if bet_yes < PLATFORM_MIN_BET or bet_no < PLATFORM_MIN_BET:
        return None

    expected_profit = allocated_capital - (bet_yes * price_yes + bet_no * price_no)

    return {
        'allocated_capital': allocated_capital,
        'bet_yes': bet_yes,
        'bet_no': bet_no,
        'platform_yes': platform_yes,
        'platform_no': platform_no,
        'price_yes': price_yes,
        'price_no': price_no,
        'expected_profit': expected_profit,
        'roi_percent': (expected_profit / allocated_capital * 100) if allocated_capital > 0 else 0
    }


def allocate_capital(
    opportunities: List[Dict],
    total_capital: float,
    strategy: AllocationStrategy = AllocationStrategy.EQUAL
) -> Dict:
    if strategy == AllocationStrategy.EQUAL:
        allocations = equal_weight_allocation(opportunities, total_capital)

    validated_allocations = []
    total_deployed = 0
    total_expected_profit = 0

    for allocation in allocations:
        bet_details = calculate_bet_amounts(
            allocation['opportunity'],
            allocation['allocated_capital']
        )

        if bet_details:
            allocation['bet_details'] = bet_details
            validated_allocations.append(allocation)
            total_deployed += bet_details['allocated_capital']
            total_expected_profit += bet_details['expected_profit']

    return {
        'allocations': validated_allocations,
        'num_opportunities': len(validated_allocations),
        'total_capital': total_capital,
        'total_deployed': total_deployed,
        'total_expected_profit': total_expected_profit,
        'overall_roi_percent': (total_expected_profit / total_deployed * 100) if total_deployed > 0 else 0
    }


