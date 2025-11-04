# CrewAI Travel Planner Microservice

## Overview
This is a multi-agent travel planning microservice based on the research paper "Orchestrating Intelligence: A CrewAI-Based Architecture for Seamless End-to-End Travel Planning" by Muhammad Umar, Abdullah Naeem, and Ammar Ahmed from FAST NUCES Islamabad.

The system implements a resilient multi-agent platform featuring explicit verification and re-planning loops, demonstrating significantly higher Failure Recovery Rates and superior policy compliance compared to baseline sequential systems.

## Architecture Components

### Core Agents
1. **Meta-Agent** - Central coordinator that orchestrates all specialized agents
2. **Flight Agent** - Handles flight search and booking coordination
3. **Hotel Agent** - Manages accommodation search and booking
4. **Weather Agent** - Provides weather forecasts and alerts
5. **Activity Agent** - Recommends and coordinates activities
6. **Verification Agent** - Monitors schema consistency and constraint validation
7. **Re-planning Engine** - Implements multi-level failure recovery

### Protocols
- **A2A Protocol** - Agent-to-Agent protocol for peer-to-peer coordination
- **MCP** - Model Context Protocol for shared contextual understanding

### Recovery Strategy
- **Level 1**: Local Recovery - Individual agents attempt domain-specific fixes
- **Level 2**: Cross-Domain Recovery - Meta-Agent coordinates changes across domains
- **Level 3**: Global Re-planning - Complete itinerary reconstruction

## Technology Stack
- **CrewAI** - Multi-agent orchestration framework
- **FastAPI** - RESTful microservice framework
- **Pydantic** - Data validation and settings management
- **OpenAI** - LLM integration for agent intelligence
- **WebSockets** - Real-time agent activity monitoring

## API Endpoints
- `POST /plan-trip` - Create comprehensive travel itinerary
- `GET /itinerary/{request_id}` - Retrieve specific itinerary
- `GET /itineraries` - List all itineraries
- `POST /simulate-failure` - Test failure recovery mechanisms
- `GET /system/health` - System health monitoring
- `GET /system/a2a-messages` - A2A protocol message history
- `GET /system/mcp-context` - MCP context snapshot
- `WS /ws` - WebSocket for real-time updates

## Running the System
The system runs on port 5000. Access the monitoring dashboard at the root URL to interact with the multi-agent system.

## Research Paper Implementation
This implementation follows the architecture described in the paper, including:
- Hierarchical task decomposition
- A2A protocol for agent communication
- MCP for context sharing
- Multi-level re-planning engine
- Comprehensive verification mechanisms

## Current State
All agents are functional with mock external APIs for demonstration. The system successfully demonstrates:
- End-to-end travel planning
- Agent coordination via A2A protocol
- Shared context via MCP
- Failure detection and recovery
- Real-time monitoring and logging
