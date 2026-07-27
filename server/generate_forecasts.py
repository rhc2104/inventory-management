"""
Generate demand forecasts derived from inventory.json.

Forecasts are derived from the inventory file rather than a separate product
catalog so the two can never drift apart. An earlier catalog-driven forecast set
left 8 of 9 forecast SKUs pointing at products that no longer existed in
inventory, which broke every join between demand and cost.

Run from the server directory:  uv run python generate_forecasts.py
"""
import json
import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Fixed seed keeps output deterministic so backend tests can assert on it
SEED = 20250927

# Stable items must stay under 2% change (tests/backend/test_misc_endpoints.py).
# Bounded well inside that so integer rounding can't push a row over the line.
STABLE_RANGE = (0.993, 1.007)
INCREASING_RANGE = (1.12, 1.45)
DECREASING_RANGE = (0.60, 0.88)

PERIOD = 'Next 3 months'


def build_forecasts(inventory):
    """Derive one forecast per inventory item, with a spread of trends."""
    rng = random.Random(SEED)

    # Items already at or below their reorder point are the ones a planner most
    # needs to see, so force them to 'increasing' to surface them as urgent.
    def is_low_stock(item):
        return item['quantity_on_hand'] <= item['reorder_point']

    low_stock = [i for i in inventory if is_low_stock(i)]
    healthy = [i for i in inventory if not is_low_stock(i)]
    rng.shuffle(healthy)

    # Split the healthy remainder so the whole set lands near 12/13/7.
    extra_increasing = max(0, 12 - len(low_stock))
    trend_by_sku = {i['sku']: 'increasing' for i in low_stock}
    for idx, item in enumerate(healthy):
        if idx < extra_increasing:
            trend_by_sku[item['sku']] = 'increasing'
        elif idx < extra_increasing + 13:
            trend_by_sku[item['sku']] = 'stable'
        else:
            trend_by_sku[item['sku']] = 'decreasing'

    forecasts = []
    for idx, item in enumerate(inventory, start=1):
        trend = trend_by_sku[item['sku']]

        # Scale demand off the reorder point so the numbers stay plausible
        # relative to how much of the item the warehouse expects to move.
        current = max(1, round(item['reorder_point'] * rng.uniform(0.8, 1.6)))

        if trend == 'increasing':
            multiplier = rng.uniform(*INCREASING_RANGE)
        elif trend == 'decreasing':
            multiplier = rng.uniform(*DECREASING_RANGE)
        else:
            multiplier = rng.uniform(*STABLE_RANGE)

        forecasted = max(0, round(current * multiplier))

        # Rounding a small 'stable' value can land it back on current, or just
        # over the 2% line. Nudge it to the nearest legal non-equal value.
        if trend == 'stable':
            forecasted = _clamp_stable(current, forecasted)

        forecasts.append({
            'id': str(idx),
            'item_sku': item['sku'],
            'item_name': item['name'],
            'current_demand': current,
            'forecasted_demand': forecasted,
            'trend': trend,
            'period': PERIOD,
        })

    return forecasts


def _clamp_stable(current, forecasted):
    """Force a stable forecast strictly inside +/-2% of current demand."""
    limit = current * 0.02
    if abs(forecasted - current) >= limit:
        # Step toward current until it's inside the band.
        direction = 1 if forecasted > current else -1
        forecasted = current + direction * max(0, int(limit) - 1 if limit >= 1 else 0)
    if forecasted == current and current > 1:
        # Keep a visible delta where the band is wide enough to allow one.
        if limit > 1:
            forecasted = current - 1
    return max(0, forecasted)


def main():
    with open(os.path.join(DATA_DIR, 'inventory.json')) as f:
        inventory = json.load(f)

    forecasts = build_forecasts(inventory)

    out_path = os.path.join(DATA_DIR, 'demand_forecasts.json')
    with open(out_path, 'w') as f:
        json.dump(forecasts, f, indent=2)
        f.write('\n')

    counts = {}
    for forecast in forecasts:
        counts[forecast['trend']] = counts.get(forecast['trend'], 0) + 1

    print(f'Generated {len(forecasts)} forecasts -> {out_path}')
    for trend in ('increasing', 'stable', 'decreasing'):
        print(f'  {trend}: {counts.get(trend, 0)}')


if __name__ == '__main__':
    main()
