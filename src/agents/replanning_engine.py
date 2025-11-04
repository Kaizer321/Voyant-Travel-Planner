from typing import Dict, Any, Optional
from datetime import datetime
from src.models.schemas import TravelItinerary, TravelRequest, PlanningStatus
from src.protocols.mcp_context import MCPContext
from src.agents.verification_agent import VerificationAgent
import asyncio


class ReplanningEngine:
    """
    Re-planning Engine: Implements multi-level recovery strategy:
    - Level 1: Local Recovery - Individual agents attempt to resolve issues
    - Level 2: Cross-Domain Recovery - Meta-Agent coordinates changes across domains
    - Level 3: Global Re-planning - Complete itinerary reconstruction
    """

    def __init__(
        self,
        meta_agent,
        verification_agent: VerificationAgent,
        mcp_context: MCPContext,
    ):
        self.meta_agent = meta_agent
        self.verification_agent = verification_agent
        self.mcp_context = mcp_context
        self.recovery_attempts = {}
        self.max_recovery_attempts = 3

    async def handle_failure(
        self,
        failure_type: str,
        failed_component: str,
        itinerary: TravelItinerary,
        request: TravelRequest,
    ) -> TravelItinerary:
        """
        Handle failures with appropriate recovery level
        """
        recovery_key = f"{request.request_id}_{failed_component}"
        attempts = self.recovery_attempts.get(recovery_key, 0)

        if attempts >= self.max_recovery_attempts:
            itinerary.status = PlanningStatus.FAILED
            itinerary.agent_logs.append(
                f"[{datetime.utcnow().isoformat()}] Re-planning Engine: Max recovery attempts reached for {failed_component}"
            )
            return itinerary

        self.recovery_attempts[recovery_key] = attempts + 1

        itinerary.agent_logs.append(
            f"[{datetime.utcnow().isoformat()}] Re-planning Engine: Attempting recovery (attempt {attempts + 1}/{self.max_recovery_attempts})"
        )

        if failure_type == "api_failure":
            return await self._level1_local_recovery(
                failed_component, itinerary, request
            )
        elif failure_type == "constraint_violation":
            return await self._level2_cross_domain_recovery(
                failed_component, itinerary, request
            )
        elif failure_type == "budget_exceeded":
            return await self._level3_global_replanning(itinerary, request)
        else:
            return await self._level2_cross_domain_recovery(
                failed_component, itinerary, request
            )

    async def _level1_local_recovery(
        self, component: str, itinerary: TravelItinerary, request: TravelRequest
    ) -> TravelItinerary:
        """
        Level 1: Individual agent attempts to resolve issues
        """
        itinerary.agent_logs.append(
            f"[{datetime.utcnow().isoformat()}] Re-planning Engine: Level 1 - Local recovery for {component}"
        )

        try:
            if component == "flight":
                await asyncio.sleep(0.5)
                new_flight = await self.meta_agent._book_outbound_flight(request)
                if new_flight:
                    itinerary.outbound_flight = new_flight
                    itinerary.agent_logs.append(
                        f"[{datetime.utcnow().isoformat()}] Re-planning Engine: Successfully recovered flight"
                    )

            elif component == "hotel":
                await asyncio.sleep(0.5)
                new_hotel = await self.meta_agent._book_hotel(request)
                if new_hotel:
                    itinerary.hotel = new_hotel
                    itinerary.agent_logs.append(
                        f"[{datetime.utcnow().isoformat()}] Re-planning Engine: Successfully recovered hotel"
                    )

            itinerary.status = PlanningStatus.COMPLETED
        except Exception as e:
            itinerary.agent_logs.append(
                f"[{datetime.utcnow().isoformat()}] Re-planning Engine: Level 1 failed - {str(e)}"
            )

        return itinerary

    async def _level2_cross_domain_recovery(
        self, component: str, itinerary: TravelItinerary, request: TravelRequest
    ) -> TravelItinerary:
        """
        Level 2: Meta-Agent coordinates changes across multiple domains
        """
        itinerary.agent_logs.append(
            f"[{datetime.utcnow().isoformat()}] Re-planning Engine: Level 2 - Cross-domain recovery"
        )

        try:
            if itinerary.outbound_flight:
                new_hotel = await self.meta_agent._book_hotel(request)
                if new_hotel:
                    itinerary.hotel = new_hotel
                    self.mcp_context.update_context(
                        "hotel", new_hotel, "replanning_engine"
                    )

            if itinerary.hotel:
                activities = await self.meta_agent._recommend_activities(
                    request, itinerary.weather_forecast
                )
                itinerary.activities = activities
                self.mcp_context.update_context(
                    "activities",
                    [a.model_dump() for a in activities],
                    "replanning_engine",
                )

            itinerary.total_cost = self.meta_agent._calculate_total_cost(itinerary)
            itinerary.remaining_budget = request.budget - itinerary.total_cost
            itinerary.status = PlanningStatus.COMPLETED

            itinerary.agent_logs.append(
                f"[{datetime.utcnow().isoformat()}] Re-planning Engine: Level 2 recovery successful"
            )

        except Exception as e:
            itinerary.agent_logs.append(
                f"[{datetime.utcnow().isoformat()}] Re-planning Engine: Level 2 failed - {str(e)}"
            )

        return itinerary

    async def _level3_global_replanning(
        self, itinerary: TravelItinerary, request: TravelRequest
    ) -> TravelItinerary:
        """
        Level 3: Complete itinerary reconstruction
        """
        itinerary.agent_logs.append(
            f"[{datetime.utcnow().isoformat()}] Re-planning Engine: Level 3 - Global re-planning initiated"
        )

        try:
            adjusted_request = TravelRequest(**request.model_dump())
            adjusted_request.budget = request.budget * 0.9

            new_itinerary = await self.meta_agent.process_travel_request(
                adjusted_request
            )

            verification = self.verification_agent.verify_itinerary(
                new_itinerary, adjusted_request.budget
            )

            if verification.is_valid:
                itinerary.agent_logs.append(
                    f"[{datetime.utcnow().isoformat()}] Re-planning Engine: Level 3 successful with reduced budget"
                )
                return new_itinerary
            else:
                itinerary.agent_logs.append(
                    f"[{datetime.utcnow().isoformat()}] Re-planning Engine: Level 3 failed - {verification.errors}"
                )

        except Exception as e:
            itinerary.agent_logs.append(
                f"[{datetime.utcnow().isoformat()}] Re-planning Engine: Level 3 failed - {str(e)}"
            )

        return itinerary

    async def adaptive_recovery(
        self, itinerary: TravelItinerary, request: TravelRequest
    ) -> TravelItinerary:
        """
        Adaptive workflow transitions based on verification results
        """
        verification = self.verification_agent.verify_itinerary(
            itinerary, request.budget
        )

        if not verification.is_valid:
            itinerary.status = PlanningStatus.RE_PLANNING
            itinerary.verification_results = verification.model_dump()

            if "budget" in str(verification.errors).lower():
                itinerary = await self.handle_failure(
                    "budget_exceeded", "budget", itinerary, request
                )
            elif "missing" in str(verification.errors).lower():
                missing_component = self._identify_missing_component(
                    verification.errors
                )
                itinerary = await self.handle_failure(
                    "constraint_violation", missing_component, itinerary, request
                )

        return itinerary

    def _identify_missing_component(self, errors: list) -> str:
        """Identify which component is missing from errors"""
        error_str = " ".join(errors).lower()
        if "flight" in error_str:
            return "flight"
        elif "hotel" in error_str:
            return "hotel"
        elif "activity" in error_str:
            return "activity"
        return "unknown"
