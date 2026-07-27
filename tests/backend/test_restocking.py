"""
Tests for restocking API endpoints (candidates and submitted restock orders).
"""
from datetime import datetime

import pytest


CANDIDATE_FIELDS = [
    "sku", "name", "category", "warehouse", "unit_cost",
    "quantity_on_hand", "reorder_point", "current_demand",
    "forecasted_demand", "trend", "growth_pct",
    "recommended_quantity", "line_cost", "urgency", "lead_time_days",
]

# Items sitting at or below their reorder point in inventory.json
KNOWN_CRITICAL_SKUS = {"TMP-201", "SRV-301", "SRV-302", "PSU-508"}

URGENCY_RANK = {"critical": 0, "watch": 1, "healthy": 2}


def _candidates(client, query=""):
    response = client.get(f"/api/restock/candidates{query}")
    assert response.status_code == 200
    return response.json()


def _first_sku_in_category(client, category):
    """Return a candidate SKU from a given category, or None."""
    for candidate in _candidates(client):
        if candidate["category"] == category:
            return candidate
    return None


class TestRestockCandidates:
    """Test suite for GET /api/restock/candidates."""

    def test_get_all_candidates(self, client):
        """Test getting all restock candidates."""
        data = _candidates(client)
        assert isinstance(data, list)
        assert len(data) > 0

        first = data[0]
        for field in CANDIDATE_FIELDS:
            assert field in first, f"Missing field {field}"

    def test_candidate_field_types(self, client):
        """Test that candidate numeric fields have proper types and ranges."""
        for candidate in _candidates(client):
            assert isinstance(candidate["quantity_on_hand"], int)
            assert isinstance(candidate["reorder_point"], int)
            assert isinstance(candidate["recommended_quantity"], int)
            assert isinstance(candidate["lead_time_days"], int)
            assert isinstance(candidate["unit_cost"], (int, float))
            assert isinstance(candidate["line_cost"], (int, float))
            assert isinstance(candidate["growth_pct"], (int, float))
            assert candidate["quantity_on_hand"] >= 0
            assert candidate["unit_cost"] >= 0

    def test_all_candidates_need_restocking(self, client):
        """Test that every candidate has a positive recommended quantity."""
        data = _candidates(client)
        for candidate in data:
            assert candidate["recommended_quantity"] > 0, \
                f"{candidate['sku']} recommended 0 units but was returned"

    def test_recommended_quantity_matches_target_rule(self, client):
        """Test recommended quantity = max(reorder_point*2, forecast) - on_hand."""
        for candidate in _candidates(client):
            target = max(candidate["reorder_point"] * 2, candidate["forecasted_demand"])
            expected = target - candidate["quantity_on_hand"]
            assert candidate["recommended_quantity"] == expected

    def test_line_cost_calculation(self, client):
        """Test that line cost is quantity times unit cost."""
        for candidate in _candidates(client):
            expected = candidate["recommended_quantity"] * candidate["unit_cost"]
            assert abs(candidate["line_cost"] - expected) < 0.01

    def test_candidates_sorted_by_urgency(self, client):
        """Test that candidates are returned most urgent first."""
        ranks = [URGENCY_RANK[c["urgency"]] for c in _candidates(client)]
        assert ranks == sorted(ranks), "Candidates are not ordered by urgency"

    def test_low_stock_items_are_critical(self, client):
        """Test that items at or below reorder point are marked critical."""
        by_sku = {c["sku"]: c for c in _candidates(client)}

        for sku in KNOWN_CRITICAL_SKUS:
            assert sku in by_sku, f"{sku} is below reorder point but not a candidate"
            assert by_sku[sku]["urgency"] == "critical"

    def test_urgency_classification_rule(self, client):
        """Test urgency thresholds against on-hand vs reorder point."""
        for candidate in _candidates(client):
            on_hand = candidate["quantity_on_hand"]
            reorder = candidate["reorder_point"]

            if on_hand <= reorder:
                assert candidate["urgency"] == "critical"
            elif on_hand <= reorder * 1.5:
                assert candidate["urgency"] == "watch"
            else:
                assert candidate["urgency"] == "healthy"

    def test_get_candidates_by_warehouse(self, client):
        """Test filtering candidates by warehouse."""
        data = _candidates(client, "?warehouse=Tokyo")
        assert len(data) > 0
        for candidate in data:
            assert candidate["warehouse"] == "Tokyo"

    def test_get_candidates_by_category(self, client):
        """Test filtering candidates by category."""
        data = _candidates(client, "?category=Actuators")
        assert len(data) > 0
        for candidate in data:
            assert candidate["category"].lower() == "actuators"

    def test_get_candidates_multiple_filters(self, client):
        """Test filtering candidates by warehouse and category together."""
        data = _candidates(client, "?warehouse=Tokyo&category=Actuators")
        for candidate in data:
            assert candidate["warehouse"] == "Tokyo"
            assert candidate["category"].lower() == "actuators"

    def test_filters_narrow_the_result_set(self, client):
        """Test that filtering returns a subset of the unfiltered candidates."""
        every = _candidates(client)
        tokyo = _candidates(client, "?warehouse=Tokyo")
        assert len(tokyo) < len(every)

    def test_all_filter_value_is_ignored(self, client):
        """Test that the sentinel value 'all' does not filter anything out."""
        every = _candidates(client)
        with_all = _candidates(client, "?warehouse=all&category=all")
        assert len(with_all) == len(every)

    def test_lead_time_matches_category(self, client):
        """Test that lead time is derived from the item's category."""
        expected_by_category = {
            "Actuators": 21,
            "Power Supplies": 14,
            "Circuit Boards": 10,
            "Sensors": 7,
            "Controllers": 7,
        }

        for candidate in _candidates(client):
            expected = expected_by_category.get(candidate["category"])
            if expected is not None:
                assert candidate["lead_time_days"] == expected

    def test_candidates_join_to_inventory(self, client):
        """Test that every candidate SKU is a real inventory item."""
        inventory = {i["sku"]: i for i in client.get("/api/inventory").json()}

        for candidate in _candidates(client):
            assert candidate["sku"] in inventory
            assert candidate["unit_cost"] == inventory[candidate["sku"]]["unit_cost"]


class TestCreateRestockOrder:
    """Test suite for POST /api/restock/orders."""

    def _payload(self, client, count=2):
        candidates = _candidates(client)[:count]
        return {
            "budget": 500000,
            "items": [
                {"sku": c["sku"], "quantity": c["recommended_quantity"]}
                for c in candidates
            ],
        }, candidates

    def test_create_restock_order(self, client):
        """Test submitting a restock order."""
        payload, candidates = self._payload(client)

        response = client.post("/api/restock/orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        for field in ["id", "order_number", "status", "items", "budget",
                      "total_value", "order_date", "expected_delivery",
                      "lead_time_days"]:
            assert field in order

        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        assert len(order["items"]) == len(candidates)

    def test_order_items_structure(self, client):
        """Test that submitted order items carry name and unit price."""
        payload, _ = self._payload(client)
        order = client.post("/api/restock/orders", json=payload).json()

        for item in order["items"]:
            assert "sku" in item
            assert "name" in item
            assert "quantity" in item
            assert "unit_price" in item
            assert isinstance(item["quantity"], int)
            assert item["quantity"] > 0

    def test_total_value_calculation(self, client):
        """Test that total value equals the sum of the line items."""
        payload, _ = self._payload(client)
        order = client.post("/api/restock/orders", json=payload).json()

        calculated = sum(i["quantity"] * i["unit_price"] for i in order["items"])
        assert abs(order["total_value"] - calculated) < 0.01

    def test_unit_price_comes_from_inventory_not_request(self, client):
        """Test that a client-supplied price is ignored in favour of inventory."""
        inventory = {i["sku"]: i for i in client.get("/api/inventory").json()}
        candidate = _candidates(client)[0]

        response = client.post("/api/restock/orders", json={
            "budget": 100000,
            # A malicious or stale client sends its own price - it must not win.
            "items": [{
                "sku": candidate["sku"],
                "quantity": 5,
                "unit_price": 0.01,
            }],
        })
        assert response.status_code == 201

        order = response.json()
        real_cost = inventory[candidate["sku"]]["unit_cost"]
        assert order["items"][0]["unit_price"] == real_cost
        assert abs(order["total_value"] - 5 * real_cost) < 0.01

    def test_lead_time_is_max_across_items(self, client):
        """Test that order lead time is the longest of its line items."""
        actuator = _first_sku_in_category(client, "Actuators")   # 21 days
        sensor = _first_sku_in_category(client, "Sensors")       # 7 days
        assert actuator and sensor, "Need one actuator and one sensor candidate"

        response = client.post("/api/restock/orders", json={
            "budget": 100000,
            "items": [
                {"sku": sensor["sku"], "quantity": 1},
                {"sku": actuator["sku"], "quantity": 1},
            ],
        })
        assert response.status_code == 201
        assert response.json()["lead_time_days"] == 21

    def test_expected_delivery_matches_lead_time(self, client):
        """Test that expected delivery is order date plus lead time."""
        payload, _ = self._payload(client)
        order = client.post("/api/restock/orders", json=payload).json()

        ordered = datetime.fromisoformat(order["order_date"])
        delivery = datetime.fromisoformat(order["expected_delivery"])
        assert (delivery - ordered).days == order["lead_time_days"]

    def test_order_numbers_increment(self, client):
        """Test that each submitted order gets a distinct order number."""
        payload, _ = self._payload(client, count=1)

        first = client.post("/api/restock/orders", json=payload).json()
        second = client.post("/api/restock/orders", json=payload).json()

        assert first["order_number"] != second["order_number"]
        assert first["id"] != second["id"]

    def test_empty_items_rejected(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restock/orders",
                               json={"budget": 1000, "items": []})
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_unknown_sku_rejected(self, client):
        """Test that an unknown SKU is rejected."""
        response = client.post("/api/restock/orders", json={
            "budget": 1000,
            "items": [{"sku": "NOPE-999", "quantity": 5}],
        })
        assert response.status_code == 400

        detail = response.json()["detail"].lower()
        assert "nope-999" in detail

    def test_non_positive_quantity_rejected(self, client):
        """Test that zero or negative quantities are rejected."""
        candidate = _candidates(client)[0]

        for bad_quantity in (0, -5):
            response = client.post("/api/restock/orders", json={
                "budget": 1000,
                "items": [{"sku": candidate["sku"], "quantity": bad_quantity}],
            })
            assert response.status_code == 400, \
                f"quantity={bad_quantity} should be rejected"


class TestListRestockOrders:
    """Test suite for GET /api/restock/orders."""

    def test_get_restock_orders(self, client):
        """Test listing submitted restock orders."""
        response = client.get("/api/restock/orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_submitted_order_appears_in_list(self, client):
        """Test that a submitted order is retrievable afterwards."""
        candidate = _candidates(client)[0]
        created = client.post("/api/restock/orders", json={
            "budget": 50000,
            "items": [{"sku": candidate["sku"], "quantity": 3}],
        }).json()

        listed = client.get("/api/restock/orders").json()
        numbers = [o["order_number"] for o in listed]
        assert created["order_number"] in numbers

    def test_orders_returned_newest_first(self, client):
        """Test that the most recently submitted order is listed first."""
        candidate = _candidates(client)[0]
        payload = {"budget": 50000,
                   "items": [{"sku": candidate["sku"], "quantity": 2}]}

        client.post("/api/restock/orders", json=payload)
        newest = client.post("/api/restock/orders", json=payload).json()

        listed = client.get("/api/restock/orders").json()
        assert listed[0]["order_number"] == newest["order_number"]


class TestRestockingDoesNotAffectExistingEndpoints:
    """Restock orders live in their own list and must not leak elsewhere."""

    def test_orders_endpoint_unaffected(self, client):
        """Test that submitting a restock order does not change /api/orders."""
        before = len(client.get("/api/orders").json())

        candidate = _candidates(client)[0]
        client.post("/api/restock/orders", json={
            "budget": 50000,
            "items": [{"sku": candidate["sku"], "quantity": 4}],
        })

        after = client.get("/api/orders").json()
        assert len(after) == before
        assert all(o["status"] != "Submitted" for o in after)

    def test_dashboard_summary_unaffected(self, client):
        """Test that dashboard aggregates ignore submitted restock orders."""
        before = client.get("/api/dashboard/summary").json()

        candidate = _candidates(client)[0]
        client.post("/api/restock/orders", json={
            "budget": 50000,
            "items": [{"sku": candidate["sku"], "quantity": 4}],
        })

        assert client.get("/api/dashboard/summary").json() == before
