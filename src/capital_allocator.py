from typing import List, Dict, Optional
from enum import Enum


class AllocationStrategy(Enum):
    EQUAL = "equal"
    ROI_WEIGHTED = "roi_weighted"
    KELLY = "kelly"


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


def roi_weighted_allocation(opportunities: List[Dict], total_capital: float) -> List[Dict]:
    if not opportunities:
        return []

    roi_values = []
    for opp in opportunities:
        best = opp['arbitrage'].get('best_strategy')
        if best:
            roi_values.append(best['roi_percent'])
        else:
            roi_values.append(0)

    total_roi = sum(roi_values)
    if total_roi == 0:
        return equal_weight_allocation(opportunities, total_capital)

    allocations = []
    for opp, roi in zip(opportunities, roi_values):
        allocated = (roi / total_roi) * total_capital
        if allocated >= PLATFORM_MIN_BET * 2:
            allocations.append({
                'opportunity': opp,
                'allocated_capital': allocated
            })

    return allocations


def kelly_allocation(opportunities: List[Dict], total_capital: float) -> List[Dict]:
    if not opportunities:
        return []

    kelly_fractions = []
    for opp in opportunities:
        best = opp['arbitrage'].get('best_strategy')
        if best and best['cost'] > 0:
            win_prob = 1.0
            odds = 1.0 / best['cost'] - 1.0
            kelly_fraction = (win_prob * odds - (1 - win_prob)) / odds
            kelly_fraction = max(0, min(kelly_fraction, 0.25))
            kelly_fractions.append(kelly_fraction)
        else:
            kelly_fractions.append(0)

    total_fraction = sum(kelly_fractions)
    if total_fraction == 0:
        return equal_weight_allocation(opportunities, total_capital)

    allocations = []
    for opp, fraction in zip(opportunities, kelly_fractions):
        allocated = (fraction / total_fraction) * total_capital
        if allocated >= PLATFORM_MIN_BET * 2:
            allocations.append({
                'opportunity': opp,
                'allocated_capital': allocated
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
        outcome_yes = "YES"
        outcome_no = "NO"
    else:
        price_yes = arb['market2_yes']
        price_no = arb['market1_no']
        platform_yes = "predict.fun"
        platform_no = "Polymarket"
        outcome_yes = "YES"
        outcome_no = "NO"

    total_price = price_yes + price_no
    if total_price == 0:
        return None

    bet_yes = allocated_capital * (price_no / total_price)
    bet_no = allocated_capital * (price_yes / total_price)

    if bet_yes < PLATFORM_MIN_BET or bet_no < PLATFORM_MIN_BET:
        return None

    expected_profit = allocated_capital - (bet_yes * price_yes + bet_no * price_no)

    return {
        'allocated_capital': allocated_capital,
        'bet_yes': bet_yes,
        'bet_no': bet_no,
        'platform_yes': platform_yes,
        'platform_no': platform_no,
        'outcome_yes': outcome_yes,
        'outcome_no': outcome_no,
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
    elif strategy == AllocationStrategy.ROI_WEIGHTED:
        allocations = roi_weighted_allocation(opportunities, total_capital)
    elif strategy == AllocationStrategy.KELLY:
        allocations = kelly_allocation(opportunities, total_capital)
    else:
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
        'total_capital': total_capital,
        'total_deployed': total_deployed,
        'total_unallocated': total_capital - total_deployed,
        'total_expected_profit': total_expected_profit,
        'overall_roi_percent': (total_expected_profit / total_deployed * 100) if total_deployed > 0 else 0,
        'num_opportunities': len(validated_allocations),
        'strategy': strategy.value
    }


def validate_allocations(allocation_result: Dict) -> List[str]:
    warnings = []

    if allocation_result['total_unallocated'] > allocation_result['total_capital'] * 0.5:
        warnings.append(
            f"More than 50% of capital (${allocation_result['total_unallocated']:.2f}) "
            f"could not be allocated due to minimum bet requirements"
        )

    if allocation_result['num_opportunities'] == 0:
        warnings.append("No opportunities could be allocated with the given capital")

    for allocation in allocation_result['allocations']:
        bet_details = allocation['bet_details']
        if bet_details['bet_yes'] < PLATFORM_MIN_BET or bet_details['bet_no'] < PLATFORM_MIN_BET:
            warnings.append(
                f"Bet amount below minimum for market: {allocation['opportunity']['market']['question'][:50]}"
            )

    return warnings

