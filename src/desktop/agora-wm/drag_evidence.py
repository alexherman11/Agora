"""Outcome assertions shared by the hidden gesture harness and its unit tests."""
import math


def assess(trace, budget_ms=100):
    """Fail closed: missing input, hooks, movement, paint or timing is not a pass."""
    assert trace['input'] == ['down', 'move', 'up'], 'incomplete mouse gesture'
    assert {'drag-start', 'drag-end'} <= set(trace['events']), 'OS move-loop events missing'
    assert trace['alive'] and trace['visible'], 'a fixture closed, hid or minimised'
    assert trace['rings'] > 0, 'no coloured drop border painted'
    assert trace['drop'] == trace['landing'], 'drop did not fill the shown landing'
    positions = trace['neighbour']
    unique = list(dict.fromkeys(tuple(p) for p in positions))
    assert len(unique) >= 4 and unique[0] != unique[-1], 'neighbour did not slide aside'
    distance = math.dist(unique[0][:2], unique[-1][:2])
    assert distance > 20, 'neighbour displacement too small'
    largest = max(math.dist(a[:2], b[:2]) for a, b in zip(positions, positions[1:]))
    assert largest < distance * .75, 'neighbour jumped instead of sliding'
    lags = trace['input_lag_ms']
    assert len(lags) >= 8 and all(0 <= x <= budget_ms for x in lags), 'fast drag input lag exceeds budget'
    costs = sorted(trace['tick_ms'])
    assert costs and costs[min(len(costs) - 1, int(len(costs) * .95))] <= 32, 'WM tick p95 exceeds 32 ms'
    assert max(costs) <= budget_ms, 'WM tick stalled'
    return {'input_lag_max_ms': round(max(lags), 2),
            'tick_p95_ms': round(costs[min(len(costs) - 1, int(len(costs) * .95))], 2),
            'neighbour_positions': len(unique), 'painted_rings': trace['rings']}
