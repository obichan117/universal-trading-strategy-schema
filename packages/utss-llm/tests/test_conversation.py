"""Tests for conversation session and builder."""

import pytest
from utss_llm.conversation import (
    ConversationResponse,
    ConversationSession,
    ConversationState,
    Option,
    PartialStrategy,
    Question,
    ResponseType,
    StrategyBuilder,
    create_session,
    delete_session,
    get_session,
)


class TestOption:
    """Tests for Option dataclass."""

    def test_option_creation(self):
        """Option should store id, label, description."""
        opt = Option(id="rsi", label="RSI", description="Relative Strength Index")
        assert opt.id == "rsi"
        assert opt.label == "RSI"
        assert opt.description == "Relative Strength Index"

    def test_option_str(self):
        """Option str should include label and description."""
        opt = Option(id="rsi", label="RSI", description="Momentum indicator")
        assert "RSI" in str(opt)
        assert "Momentum" in str(opt)


class TestQuestion:
    """Tests for Question dataclass."""

    def test_question_with_options(self):
        """Question should have options."""
        q = Question(
            id="test",
            text="Choose one",
            options=[
                Option(id="a", label="A"),
                Option(id="b", label="B"),
            ],
        )
        assert q.has_options
        assert len(q.options) == 2

    def test_question_without_options(self):
        """Question can be free-form."""
        q = Question(id="test", text="Enter value")
        assert not q.has_options


class TestPartialStrategy:
    """Tests for PartialStrategy."""

    def test_to_utss_dict_minimal(self):
        """Should generate minimal valid structure."""
        ps = PartialStrategy(name="Test Strategy")
        result = ps.to_utss_dict()

        assert "info" in result
        assert result["info"]["name"] == "Test Strategy"
        assert result["info"]["id"] == "test_strategy"

    def test_to_utss_dict_with_universe(self):
        """Should include universe if set."""
        ps = PartialStrategy(
            name="Test",
            universe_type="static",
            symbols=["AAPL", "MSFT"],
        )
        result = ps.to_utss_dict()

        assert "universe" in result
        assert result["universe"]["type"] == "static"
        assert result["universe"]["symbols"] == ["AAPL", "MSFT"]

    def test_to_utss_dict_with_entry_rule(self):
        """Should generate entry rule if indicator set."""
        ps = PartialStrategy(
            name="RSI Strategy",
            entry_indicator="RSI",
            entry_threshold=30,
            entry_operator="<",
            sizing_type="percent_of_equity",
            sizing_value=10,
        )
        result = ps.to_utss_dict()

        assert "rules" in result
        assert len(result["rules"]) >= 1
        assert result["rules"][0]["when"]["type"] == "comparison"

    def test_to_utss_dict_with_constraints(self):
        """Should include constraints if set."""
        ps = PartialStrategy(
            name="Test",
            stop_loss_pct=5,
            take_profit_pct=15,
            max_positions=10,
        )
        result = ps.to_utss_dict()

        assert "constraints" in result
        assert result["constraints"]["stop_loss"]["percentage"] == 5
        assert result["constraints"]["take_profit"]["percentage"] == 15
        assert result["constraints"]["max_positions"] == 10


class TestConversationState:
    """Tests for ConversationState."""

    def test_initial_state(self):
        """Initial state should be empty."""
        state = ConversationState()
        assert state.current_step == "initial"
        assert not state.is_complete
        assert len(state.history) == 0

    def test_add_turn(self):
        """Should track conversation history."""
        state = ConversationState()
        state.add_turn("user", "Hello")
        state.add_turn("assistant", "Hi there")

        assert len(state.history) == 2
        assert state.history[0].role == "user"
        assert state.history[1].role == "assistant"

    def test_last_question(self):
        """Should return last question asked."""
        state = ConversationState()
        q = Question(id="test", text="Test?")
        state.add_turn("assistant", "Question:", question=q)

        assert state.last_question == q


class TestStrategyBuilder:
    """Tests for StrategyBuilder."""

    def test_get_initial_question(self):
        """Should return strategy type question."""
        builder = StrategyBuilder()
        response = builder.get_initial_question()

        assert response.type == ResponseType.QUESTION
        assert response.question is not None
        assert response.question.id == "strategy_type"

    def test_process_strategy_type(self):
        """Should advance to universe question."""
        builder = StrategyBuilder()
        state = ConversationState()
        state.current_step = "strategy_type"

        response = builder.process_answer(state, "mean_reversion")

        assert state.partial_strategy.name == "Mean Reversion Strategy"
        assert response.question.id == "universe_type"

    def test_full_guided_flow(self):
        """Should complete full flow with guided answers."""
        builder = StrategyBuilder()
        state = ConversationState()
        state.current_step = "strategy_type"

        # Strategy type
        response = builder.process_answer(state, "mean_reversion")
        assert response.question.id == "universe_type"

        # Universe type
        response = builder.process_answer(state, "static")
        assert response.question.id == "symbols"

        # Symbols
        response = builder.process_answer(state, "AAPL, MSFT")
        assert response.question is not None

        # Entry indicator
        response = builder.process_answer(state, "RSI")

        # Continue through the flow...
        # (simplified test - just checking it doesn't crash)


class TestConversationSession:
    """Tests for ConversationSession."""

    @pytest.mark.asyncio
    async def test_start_conversation(self):
        """Should return initial question."""
        session = ConversationSession()
        response = await session.start()

        assert response.type == ResponseType.QUESTION
        assert response.question is not None

    @pytest.mark.asyncio
    async def test_answer_numeric(self):
        """Should accept numeric answers."""
        session = ConversationSession()
        await session.start()

        # Answer with number (1 = first option)
        response = await session.answer("1")
        assert response.type == ResponseType.QUESTION

    @pytest.mark.asyncio
    async def test_answer_option_id(self):
        """Should accept option id answers."""
        session = ConversationSession()
        await session.start()

        response = await session.answer("mean_reversion")
        assert response.type == ResponseType.QUESTION
        assert session.state.partial_strategy.name == "Mean Reversion Strategy"

    def test_get_preview(self):
        """Should return YAML preview."""
        session = ConversationSession()
        session.state.partial_strategy.name = "Test"

        preview = session.get_preview()
        assert "name: Test" in preview

    @pytest.mark.asyncio
    async def test_revise_strategy(self):
        """Should allow revision of strategy."""
        session = ConversationSession()
        session.state.partial_strategy.entry_threshold = 30

        await session.revise("change RSI entry to 25")

        assert session.state.partial_strategy.entry_threshold == 25


class TestSessionManagement:
    """Tests for session storage functions."""

    def test_create_and_get_session(self):
        """Should create and retrieve session."""
        session = create_session()
        retrieved = get_session(session.session_id)

        assert retrieved is session

    def test_delete_session(self):
        """Should delete session."""
        session = create_session()
        session_id = session.session_id

        result = delete_session(session_id)
        assert result is True

        assert get_session(session_id) is None

    def test_get_nonexistent_session(self):
        """Should return None for unknown session."""
        assert get_session("nonexistent") is None


class TestConversationResponse:
    """Tests for ConversationResponse."""

    def test_is_complete(self):
        """Should identify complete response."""
        response = ConversationResponse(
            type=ResponseType.COMPLETE,
            message="Done!",
            strategy_yaml="info: ...",
        )
        assert response.is_complete

    def test_needs_input(self):
        """Should identify when input needed."""
        response = ConversationResponse(
            type=ResponseType.QUESTION,
            message="Choose:",
            question=Question(id="test", text="?"),
        )
        assert response.needs_input
        assert not response.is_complete


class TestSmartStartExtraction:
    """Tests for smart start strategy extraction."""

    def test_extract_json_from_code_block(self):
        """Should extract JSON from markdown code block."""
        session = ConversationSession()
        content = '''Here's the analysis:
```json
{"strategy_type": "mean_reversion", "indicators": ["RSI"]}
```'''
        result = session._extract_json(content)

        assert result is not None
        assert result["strategy_type"] == "mean_reversion"
        assert "RSI" in result["indicators"]

    def test_extract_json_plain(self):
        """Should extract plain JSON."""
        session = ConversationSession()
        content = '{"strategy_type": "trend_following"}'
        result = session._extract_json(content)

        assert result is not None
        assert result["strategy_type"] == "trend_following"

    def test_extract_json_invalid(self):
        """Should return None for invalid JSON."""
        session = ConversationSession()
        result = session._extract_json("Not JSON at all")

        assert result is None

    def test_prefill_strategy_type(self):
        """Should prefill strategy type from extraction."""
        session = ConversationSession()
        extracted = {"strategy_type": "mean_reversion"}

        session._prefill_strategy(extracted)

        assert session.state.partial_strategy.name == "Mean Reversion Strategy"
        assert "oversold" in session.state.partial_strategy.description.lower()

    def test_prefill_indicators(self):
        """Should prefill indicators from extraction."""
        session = ConversationSession()
        extracted = {"indicators": ["RSI", "MACD"]}

        session._prefill_strategy(extracted)

        assert session.state.partial_strategy.entry_indicator == "RSI"
        assert session.state.partial_strategy.exit_indicator == "MACD"

    def test_prefill_single_indicator(self):
        """Should use same indicator for entry and exit if only one given."""
        session = ConversationSession()
        extracted = {"indicators": ["RSI"]}

        session._prefill_strategy(extracted)

        assert session.state.partial_strategy.entry_indicator == "RSI"
        assert session.state.partial_strategy.exit_indicator == "RSI"

    def test_prefill_thresholds(self):
        """Should prefill thresholds from extraction."""
        session = ConversationSession()
        extracted = {
            "entry_threshold": 30,
            "exit_threshold": 70,
        }

        session._prefill_strategy(extracted)

        assert session.state.partial_strategy.entry_threshold == 30.0
        assert session.state.partial_strategy.exit_threshold == 70.0

    def test_prefill_symbols(self):
        """Should prefill symbols from extraction."""
        session = ConversationSession()
        extracted = {"symbols": ["aapl", "msft"]}

        session._prefill_strategy(extracted)

        assert session.state.partial_strategy.universe_type == "static"
        assert session.state.partial_strategy.symbols == ["AAPL", "MSFT"]

    def test_prefill_risk_management(self):
        """Should prefill stop loss and position size."""
        session = ConversationSession()
        extracted = {
            "stop_loss": 5,
            "position_size": 10,
        }

        session._prefill_strategy(extracted)

        assert session.state.partial_strategy.stop_loss_pct == 5.0
        assert session.state.partial_strategy.sizing_value == 10.0

    def test_skip_to_unanswered_strategy_type(self):
        """Should start at strategy type if nothing filled."""
        session = ConversationSession()

        response = session._skip_to_unanswered()

        assert response.type == ResponseType.QUESTION
        assert response.question.id == "strategy_type"

    def test_skip_to_unanswered_universe(self):
        """Should skip to universe if strategy type filled."""
        session = ConversationSession()
        session.state.partial_strategy.name = "Test Strategy"

        response = session._skip_to_unanswered()

        assert response.question.id == "universe_type"

    def test_skip_to_confirm_when_complete(self):
        """Should show preview if most fields filled."""
        session = ConversationSession()
        ps = session.state.partial_strategy
        ps.name = "RSI Strategy"
        ps.universe_type = "static"
        ps.symbols = ["AAPL"]
        ps.entry_indicator = "RSI"
        ps.entry_threshold = 30
        ps.exit_indicator = "RSI"
        ps.exit_threshold = 70
        ps.sizing_value = 10

        response = session._skip_to_unanswered()

        assert response.type == ResponseType.CONFIRMATION
        assert response.preview_yaml is not None


class TestKeywordRevision:
    """Tests for keyword-based revision."""

    def test_revise_rsi_entry(self):
        """Should revise RSI entry threshold."""
        session = ConversationSession()
        session.state.partial_strategy.entry_threshold = 30

        session._keyword_revise("change RSI entry to 25")

        assert session.state.partial_strategy.entry_threshold == 25

    def test_revise_rsi_exit(self):
        """Should revise RSI exit threshold."""
        session = ConversationSession()
        session.state.partial_strategy.exit_threshold = 70

        session._keyword_revise("set RSI exit to 75")

        assert session.state.partial_strategy.exit_threshold == 75

    def test_revise_stop_loss(self):
        """Should revise stop loss."""
        session = ConversationSession()
        session.state.partial_strategy.stop_loss_pct = 5

        session._keyword_revise("change stop loss to 7%")

        assert session.state.partial_strategy.stop_loss_pct == 7

    def test_revise_take_profit(self):
        """Should revise take profit."""
        session = ConversationSession()

        session._keyword_revise("set take profit to 20%")

        assert session.state.partial_strategy.take_profit_pct == 20

    def test_revise_position_size(self):
        """Should revise position size."""
        session = ConversationSession()
        session.state.partial_strategy.sizing_value = 10

        session._keyword_revise("change position size to 15%")

        assert session.state.partial_strategy.sizing_value == 15

    def test_revise_max_positions(self):
        """Should revise max positions."""
        session = ConversationSession()
        session.state.partial_strategy.max_positions = 5

        session._keyword_revise("set max positions to 8")

        assert session.state.partial_strategy.max_positions == 8


class TestApplyUpdates:
    """Tests for applying LLM-extracted updates."""

    def test_apply_entry_threshold(self):
        """Should apply entry threshold update."""
        session = ConversationSession()
        updates = {"entry_threshold": 25}

        session._apply_updates(updates)

        assert session.state.partial_strategy.entry_threshold == 25.0

    def test_apply_exit_threshold(self):
        """Should apply exit threshold update."""
        session = ConversationSession()
        updates = {"exit_threshold": 75}

        session._apply_updates(updates)

        assert session.state.partial_strategy.exit_threshold == 75.0

    def test_apply_stop_loss(self):
        """Should apply stop loss update."""
        session = ConversationSession()
        updates = {"stop_loss_pct": 8}

        session._apply_updates(updates)

        assert session.state.partial_strategy.stop_loss_pct == 8.0

    def test_apply_indicator(self):
        """Should apply indicator update (uppercase)."""
        session = ConversationSession()
        updates = {"entry_indicator": "macd"}

        session._apply_updates(updates)

        assert session.state.partial_strategy.entry_indicator == "MACD"

    def test_apply_null_ignored(self):
        """Should ignore null values."""
        session = ConversationSession()
        session.state.partial_strategy.entry_threshold = 30
        updates = {"entry_threshold": None}

        session._apply_updates(updates)

        assert session.state.partial_strategy.entry_threshold == 30
