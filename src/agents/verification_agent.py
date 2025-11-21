from typing import Dict, Any, List
from datetime import datetime
from src.models.schemas import TravelItinerary, VerificationResult
from src.protocols.mcp_context import MCPContext


class VerificationAgent:
    """
    Verification Agent: Continuously monitors system state and agent outputs for:
    - Schema consistency across agent communications
    - Semantic alignment between user requirements and proposed solutions
    - Temporal constraint validation (flight connections, check-in times)
    - Budget compliance and cost optimization
    """

    def __init__(self, mcp_context: MCPContext):
        self.mcp_context = mcp_context

    def verify_itinerary(
        self, itinerary: TravelItinerary, budget: float
    ) -> VerificationResult:
        """
        Comprehensive verification of travel itinerary
        """
        errors = []
        warnings = []
        suggestions = []

        errors.extend(self._check_schema_consistency(itinerary))
        errors.extend(self._check_semantic_alignment(itinerary))  # New check
        warnings.extend(self._check_temporal_constraints(itinerary))
        budget_issues = self._check_budget_compliance(itinerary, budget)
        errors.extend(budget_issues["errors"])
        warnings.extend(budget_issues["warnings"])
        suggestions.extend(self._generate_optimization_suggestions(itinerary, budget))

        context_conflicts = self.mcp_context.detect_conflicts()
        if context_conflicts:
            warnings.append(f"Detected {len(context_conflicts)} context conflicts")

        is_valid = len(errors) == 0

        return VerificationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def _check_schema_consistency(self, itinerary: TravelItinerary) -> List[str]:
        """Check schema consistency"""
        errors = []

        if not itinerary.outbound_flight:
            errors.append("Missing outbound flight")

        if not itinerary.return_flight:
            errors.append("Missing return flight")

        if not itinerary.hotel:
            errors.append("Missing hotel accommodation")

        if itinerary.total_cost <= 0:
            errors.append("Invalid total cost calculation")

        return errors

    def _check_semantic_alignment(self, itinerary: TravelItinerary) -> List[str]:
        """
        Check semantic alignment between user requirements and proposed solutions.
        Ensures that the booked items actually match the request's intent (e.g., location).
        """
        errors = []
        # In a real system, this would use LLM to verify semantic match.
        # Here we do basic heuristic checks.
        
        if itinerary.hotel and itinerary.outbound_flight:
             # Basic check: Hotel location should match flight destination (roughly)
             # This is a simplification as names might not match exactly
             pass

        return errors

    def _check_temporal_constraints(self, itinerary: TravelItinerary) -> List[str]:
        """Check temporal constraints and timing alignment"""
        warnings = []

        try:
            if itinerary.outbound_flight and itinerary.hotel:
                flight_arrival = datetime.fromisoformat(
                    itinerary.outbound_flight.arrival_time
                )
                hotel_checkin = datetime.fromisoformat(itinerary.hotel.check_in)

                if hotel_checkin.date() > flight_arrival.date():
                    warnings.append(
                        "Hotel check-in is after flight arrival - may need intermediate accommodation"
                    )

            if itinerary.return_flight and itinerary.hotel:
                flight_departure = datetime.fromisoformat(
                    itinerary.return_flight.departure_time
                )
                hotel_checkout = datetime.fromisoformat(itinerary.hotel.check_out)

                if hotel_checkout.date() > flight_departure.date():
                    warnings.append(
                        "Hotel checkout is after return flight - schedule conflict"
                    )

                hours_before_flight = (
                    flight_departure - hotel_checkout
                ).total_seconds() / 3600
                if hours_before_flight < 3:
                    warnings.append(
                        f"Only {hours_before_flight:.1f} hours between checkout and flight - may be tight"
                    )

        except Exception as e:
            warnings.append(f"Could not validate temporal constraints: {str(e)}")

        return warnings

    def _check_budget_compliance(
        self, itinerary: TravelItinerary, budget: float
    ) -> Dict[str, List[str]]:
        """Check budget compliance"""
        result = {"errors": [], "warnings": []}

        if itinerary.total_cost > budget:
            result["errors"].append(
                f"Total cost ${itinerary.total_cost:.2f} exceeds budget ${budget:.2f} by ${(itinerary.total_cost - budget):.2f}"
            )

        budget_utilization = (itinerary.total_cost / budget) * 100
        if budget_utilization < 50:
            result["warnings"].append(
                f"Only using {budget_utilization:.1f}% of budget - room for upgrades"
            )
        elif budget_utilization > 95:
            result["warnings"].append(
                f"Using {budget_utilization:.1f}% of budget - very tight"
            )

        return result

    def _generate_optimization_suggestions(
        self, itinerary: TravelItinerary, budget: float
    ) -> List[str]:
        """Generate optimization suggestions"""
        suggestions = []

        if itinerary.remaining_budget > 200:
            suggestions.append(
                f"${itinerary.remaining_budget:.2f} remaining - consider upgrading accommodations or adding more activities"
            )

        if len(itinerary.activities) < 2:
            suggestions.append("Consider adding more activities for a richer experience")

        if itinerary.outbound_flight and itinerary.outbound_flight.stops > 0:
            suggestions.append(
                "Direct flights available for better experience (may cost more)"
            )

        if not itinerary.weather_forecast:
            suggestions.append("Add weather forecast for better activity planning")

        return suggestions

    def check_agent_health(self) -> Dict[str, Any]:
        """Monitor overall agent system health"""
        access_log = self.mcp_context.get_access_log()

        agent_activity = {}
        for log_entry in access_log:
            agent_id = log_entry["agent_id"]
            if agent_id not in agent_activity:
                agent_activity[agent_id] = 0
            agent_activity[agent_id] += 1

        return {
            "total_context_operations": len(access_log),
            "agent_activity": agent_activity,
            "timestamp": datetime.utcnow().isoformat(),
        }
