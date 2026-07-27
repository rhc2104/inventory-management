"""
Tests for reports API endpoints.
"""
import pytest


def orders_matching(client, **filters):
    """Fetch orders through the orders endpoint using the same filters.

    Reports are aggregates over the same order set, so /api/orders is the
    reference the aggregates must agree with.
    """
    params = "&".join(f"{k}={v}" for k, v in filters.items())
    return client.get(f"/api/orders?{params}").json()


class TestQuarterlyReports:
    """Test suite for /api/reports/quarterly."""

    def test_get_quarterly_reports(self, client):
        """Test getting quarterly reports."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        first = data[0]
        assert "quarter" in first
        assert "total_orders" in first
        assert "total_revenue" in first
        assert "avg_order_value" in first
        assert "fulfillment_rate" in first

    def test_quarter_labels_are_derived_from_dates(self, client):
        """Test that quarter labels follow Q<N>-<YYYY> and match the data."""
        data = client.get("/api/reports/quarterly").json()

        for quarter in data:
            label = quarter["quarter"]
            assert label.startswith("Q")
            number, year = label.split("-")
            assert number in ("Q1", "Q2", "Q3", "Q4")
            assert year.isdigit() and len(year) == 4

    def test_quarterly_results_sorted(self, client):
        """Test that quarters come back in chronological order."""
        data = client.get("/api/reports/quarterly").json()
        labels = [q["quarter"] for q in data]
        assert labels == sorted(labels)

    def test_fulfillment_rate_always_present(self, client):
        """Test that fulfillment_rate is always set, never omitted."""
        data = client.get("/api/reports/quarterly").json()

        for quarter in data:
            assert isinstance(quarter["fulfillment_rate"], (int, float))
            assert 0 <= quarter["fulfillment_rate"] <= 100

    def test_avg_order_value_calculation(self, client):
        """Test that avg_order_value equals revenue divided by order count."""
        data = client.get("/api/reports/quarterly").json()

        for quarter in data:
            expected = quarter["total_revenue"] / quarter["total_orders"]
            assert abs(quarter["avg_order_value"] - expected) < 0.01

    def test_totals_match_orders_endpoint(self, client):
        """Test that quarterly totals aggregate the same orders /api/orders returns."""
        all_orders = client.get("/api/orders").json()
        data = client.get("/api/reports/quarterly").json()

        assert sum(q["total_orders"] for q in data) == len(all_orders)

        expected_revenue = sum(o["total_value"] for o in all_orders)
        actual_revenue = sum(q["total_revenue"] for q in data)
        assert abs(actual_revenue - expected_revenue) < 0.01

    def test_filter_by_warehouse(self, client):
        """Test filtering quarterly reports by warehouse."""
        response = client.get("/api/reports/quarterly?warehouse=Tokyo")
        assert response.status_code == 200

        data = response.json()
        expected = orders_matching(client, warehouse="Tokyo")

        assert sum(q["total_orders"] for q in data) == len(expected)
        assert sum(q["total_orders"] for q in data) < len(client.get("/api/orders").json())

    def test_filter_by_category(self, client):
        """Test filtering quarterly reports by category."""
        response = client.get("/api/reports/quarterly?category=sensors")
        assert response.status_code == 200

        data = response.json()
        expected = orders_matching(client, category="sensors")
        assert sum(q["total_orders"] for q in data) == len(expected)

    def test_filter_by_status(self, client):
        """Test filtering quarterly reports by status."""
        response = client.get("/api/reports/quarterly?status=delivered")
        assert response.status_code == 200

        data = response.json()
        expected = orders_matching(client, status="delivered")
        assert sum(q["total_orders"] for q in data) == len(expected)

        # Every remaining order is delivered, so fulfillment is total
        for quarter in data:
            assert quarter["fulfillment_rate"] == 100.0

    def test_filter_by_month_narrows_to_one_quarter(self, client):
        """Test that a single-month filter leaves only that month's quarter."""
        response = client.get("/api/reports/quarterly?month=2025-02")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["quarter"] == "Q1-2025"

    def test_filter_by_quarter(self, client):
        """Test filtering quarterly reports by quarter."""
        response = client.get("/api/reports/quarterly?month=Q3-2025")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["quarter"] == "Q3-2025"

    def test_multiple_filters(self, client):
        """Test combining filters on quarterly reports."""
        response = client.get(
            "/api/reports/quarterly?warehouse=London&category=sensors&status=delivered"
        )
        assert response.status_code == 200

        data = response.json()
        expected = orders_matching(
            client, warehouse="London", category="sensors", status="delivered"
        )
        assert sum(q["total_orders"] for q in data) == len(expected)

    def test_filter_matching_nothing_returns_empty(self, client):
        """Test that an unmatched filter returns an empty list, not an error."""
        response = client.get("/api/reports/quarterly?warehouse=Atlantis")
        assert response.status_code == 200
        assert response.json() == []

    def test_all_is_treated_as_no_filter(self, client):
        """Test that 'all' disables a filter rather than matching literally."""
        unfiltered = client.get("/api/reports/quarterly").json()
        response = client.get(
            "/api/reports/quarterly?warehouse=all&category=all&status=all&month=all"
        )
        assert response.status_code == 200
        assert response.json() == unfiltered


class TestMonthlyTrendReports:
    """Test suite for /api/reports/monthly-trends."""

    def test_get_monthly_trends(self, client):
        """Test getting monthly trends."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        first = data[0]
        assert "month" in first
        assert "order_count" in first
        assert "revenue" in first

    def test_month_format_and_ordering(self, client):
        """Test that months are YYYY-MM and chronologically ordered."""
        data = client.get("/api/reports/monthly-trends").json()

        months = [m["month"] for m in data]
        assert months == sorted(months)

        for month in months:
            year, number = month.split("-")
            assert year.isdigit() and len(year) == 4
            assert 1 <= int(number) <= 12

    def test_totals_match_orders_endpoint(self, client):
        """Test that monthly totals aggregate the same orders /api/orders returns."""
        all_orders = client.get("/api/orders").json()
        data = client.get("/api/reports/monthly-trends").json()

        assert sum(m["order_count"] for m in data) == len(all_orders)

        expected_revenue = sum(o["total_value"] for o in all_orders)
        actual_revenue = sum(m["revenue"] for m in data)
        assert abs(actual_revenue - expected_revenue) < 0.01

    def test_filter_by_warehouse(self, client):
        """Test filtering monthly trends by warehouse."""
        response = client.get("/api/reports/monthly-trends?warehouse=Tokyo")
        assert response.status_code == 200

        data = response.json()
        expected = orders_matching(client, warehouse="Tokyo")
        assert sum(m["order_count"] for m in data) == len(expected)

    def test_filter_by_category(self, client):
        """Test filtering monthly trends by category."""
        response = client.get("/api/reports/monthly-trends?category=controllers")
        assert response.status_code == 200

        data = response.json()
        expected = orders_matching(client, category="controllers")
        assert sum(m["order_count"] for m in data) == len(expected)

    def test_filter_by_status(self, client):
        """Test filtering monthly trends by status."""
        response = client.get("/api/reports/monthly-trends?status=shipped")
        assert response.status_code == 200

        data = response.json()
        expected = orders_matching(client, status="shipped")
        assert sum(m["order_count"] for m in data) == len(expected)

    def test_filter_by_month_returns_single_month(self, client):
        """Test that a month filter narrows the trend to that month."""
        response = client.get("/api/reports/monthly-trends?month=2025-06")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["month"] == "2025-06"

    def test_filter_by_quarter_returns_three_months(self, client):
        """Test that a quarter filter narrows the trend to that quarter's months."""
        response = client.get("/api/reports/monthly-trends?month=Q2-2025")
        assert response.status_code == 200

        data = response.json()
        assert [m["month"] for m in data] == ["2025-04", "2025-05", "2025-06"]

    def test_multiple_filters(self, client):
        """Test combining filters on monthly trends."""
        response = client.get(
            "/api/reports/monthly-trends?warehouse=Tokyo&category=sensors"
        )
        assert response.status_code == 200

        data = response.json()
        expected = orders_matching(client, warehouse="Tokyo", category="sensors")
        assert sum(m["order_count"] for m in data) == len(expected)

    def test_filter_matching_nothing_returns_empty(self, client):
        """Test that an unmatched filter returns an empty list, not an error."""
        response = client.get("/api/reports/monthly-trends?category=Unobtainium")
        assert response.status_code == 200
        assert response.json() == []

    def test_all_is_treated_as_no_filter(self, client):
        """Test that 'all' disables a filter rather than matching literally."""
        unfiltered = client.get("/api/reports/monthly-trends").json()
        response = client.get(
            "/api/reports/monthly-trends?warehouse=all&category=all&status=all&month=all"
        )
        assert response.status_code == 200
        assert response.json() == unfiltered


class TestReportsConsistency:
    """Cross-endpoint checks between the two report views."""

    def test_quarterly_and_monthly_agree_on_revenue(self, client):
        """Test that both report views total to the same revenue."""
        quarterly = client.get("/api/reports/quarterly").json()
        monthly = client.get("/api/reports/monthly-trends").json()

        assert abs(
            sum(q["total_revenue"] for q in quarterly)
            - sum(m["revenue"] for m in monthly)
        ) < 0.01

    def test_quarterly_and_monthly_agree_under_filters(self, client):
        """Test that both report views stay in agreement once filtered."""
        query = "warehouse=London&status=delivered"
        quarterly = client.get(f"/api/reports/quarterly?{query}").json()
        monthly = client.get(f"/api/reports/monthly-trends?{query}").json()

        assert sum(q["total_orders"] for q in quarterly) == sum(
            m["order_count"] for m in monthly
        )

    def test_submitted_restock_orders_do_not_leak_into_reports(self, client):
        """Test that restock orders stay out of the historical reports."""
        before = client.get("/api/reports/monthly-trends").json()

        candidates = client.get("/api/restock/candidates").json()
        client.post(
            "/api/restock/orders",
            json={
                "budget": 1000000,
                "items": [
                    {"sku": candidates[0]["sku"], "quantity": 5}
                ],
            },
        )

        after = client.get("/api/reports/monthly-trends").json()
        assert after == before
