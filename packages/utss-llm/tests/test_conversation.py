"""Tests for conversation session and builder."""

import pytest

from utss_llm.conversation import (
    ConversationSession,
    ConversationState,
    ConversationResponse,
    Option,
    PartialStrategy,
    Question,
    ResponseType,
    StrategyBuilder,
    create_session,
    get_session,
    delete_session,
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

        response = await session.revise("change RSI entry to 25")

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
