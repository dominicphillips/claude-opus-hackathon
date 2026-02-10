"""StorySpark — AI-Powered Character Studio for Parents."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text

from app.api.routes import router
from app.api.agent_routes import router as agent_router
from app.core.database import engine
from app.models import Base
from app.models.models import Character, Child, Parent, Scenario, ScenarioType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_data():
    """Seed the database with Frog & Toad characters and scenario templates."""
    from app.core.database import async_session

    async with async_session() as db:
        # Check if already seeded
        result = await db.execute(select(Character).limit(1))
        if result.scalar_one_or_none():
            logger.info("Database already seeded")
            return

        logger.info("Seeding database...")

        # --- Characters ---
        frog = Character(
            name="Frog",
            show_name="Frog & Toad",
            personality="Optimistic, adventurous, encouraging, gentle leader. Frog sees the best in every situation and every friend. He is patient, curious about the world, and finds joy in small things like a sunny day or a garden growing.",
            speech_pattern="Warm and enthusiastic. Uses nature metaphors frequently. Asks gentle questions to encourage others. Speaks with a calm confidence. Loves to start sentences with 'You know what, ...' or 'I was just thinking...' Often relates things back to friendship.",
            themes="Friendship, bravery, trying new things, appreciating nature, helping others, the joy of small moments",
            system_prompt="""You are Frog from the Apple TV+ show "Frog & Toad," based on Arnold Lobel's beloved books. You are an optimistic, gentle, and encouraging friend. You love nature, gardening, swimming, and adventures — but what you love most is your friendship with Toad.

Key traits:
- You always see the bright side
- You encourage others with warmth, never pressure
- You love telling stories about your adventures
- You speak with gentle enthusiasm
- You often reference your garden, the pond, or the changing seasons
- Your friendship with Toad is the center of your world""",
            voice_config={
                "provider": "openai",
                "voice": "ash",
                "speed": 1.0,
                "base_emotion": "warm",
            },
            avatar_url="/characters/frog.png",
        )

        toad = Character(
            name="Toad",
            show_name="Frog & Toad",
            personality="Cautious, loyal, endearing worrier who is ultimately brave. Toad overthinks things but always comes through for his friends. He finds comfort in familiar things — his house, his armchair, cookies — but Frog helps him discover new joys.",
            speech_pattern="Hesitant at first, then determined. Self-deprecating humor. Heartfelt and earnest. Often says 'Oh dear' or 'Well, I suppose...' before surprising himself with bravery. Speaks a bit slower than Frog, with thoughtful pauses.",
            themes="Overcoming fear, the courage of trying, comfort in friendship, self-acceptance, the reward of effort",
            system_prompt="""You are Toad from the Apple TV+ show "Frog & Toad," based on Arnold Lobel's beloved books. You are a lovable, slightly anxious character who is braver than you think. You love your cozy home, cookies, and most of all, your best friend Frog.

Key traits:
- You worry about things but always find your courage
- You are deeply loyal and caring
- You speak hesitantly at first but grow more confident
- You love cookies, your armchair, and staying cozy
- You sometimes say "Oh dear" when worried
- You are always honest about your feelings
- Your friendship with Frog means everything to you""",
            voice_config={
                "provider": "openai",
                "voice": "ballad",
                "speed": 0.95,
                "base_emotion": "warm",
            },
            avatar_url="/characters/toad.png",
        )

        db.add_all([frog, toad])

        # --- Scenarios ---
        scenarios = [
            Scenario(
                type=ScenarioType.CHORE_MOTIVATION,
                name="Chore Motivation",
                description="Character encourages the child to do a specific chore with warmth and a relatable story",
                structure=[
                    "Character-authentic greeting using child's name",
                    "Relate to the chore through a show-relevant anecdote or memory",
                    "Encourage the child specifically and make it feel achievable",
                    "End with warmth — promise of satisfaction or tie back to friendship/nature theme",
                ],
                example_prompt="Frog motivates Thomas to clean his room and put away his Legos",
                icon="sparkles",
            ),
            Scenario(
                type=ScenarioType.STORYTELLING,
                name="Storytelling Prompt",
                description="Character starts a story and invites the child to imagine what happens next",
                structure=[
                    "Character warmly sets the scene in their world",
                    "Introduces a gentle problem, mystery, or beginning of an adventure",
                    "Pauses and asks the child: 'What do you think happens next?'",
                    "Encourages the child's imagination with a warm, open prompt",
                ],
                example_prompt="Toad starts a story about finding a mysterious letter and asks Thomas what it says",
                icon="book-open",
            ),
            Scenario(
                type=ScenarioType.EDUCATIONAL,
                name="Educational Moment",
                description="Character teaches a concept naturally through their experience in the show's world",
                structure=[
                    "Character notices something interesting in their world",
                    "Explains a concept naturally through their own experience",
                    "Connects it to the child's world",
                    "Asks an engaging question to spark curiosity",
                ],
                example_prompt="Frog teaches Thomas about how gardens grow through the seasons",
                icon="lightbulb",
            ),
            Scenario(
                type=ScenarioType.POSITIVE_REINFORCEMENT,
                name="Celebrate an Achievement",
                description="Character celebrates something the child did well with genuine warmth",
                structure=[
                    "Excited, authentic greeting",
                    "Specifically names what the child did well",
                    "Relates it to the character's own experience with effort and trying",
                    "Expression of genuine pride, warmth, and friendship",
                ],
                example_prompt="Toad celebrates Thomas for being brave at the dentist",
                icon="trophy",
            ),
            Scenario(
                type=ScenarioType.BEDTIME,
                name="Bedtime Wind-Down",
                description="Character says goodnight with warmth, coziness, and gentle imagery",
                structure=[
                    "Gentle, quiet greeting",
                    "Reflect on something positive about the day",
                    "Cozy, calming imagery from the show's world",
                    "Warm, loving goodnight",
                ],
                example_prompt="Frog says goodnight to Thomas after a big day",
                icon="moon",
            ),
        ]

        db.add_all(scenarios)

        # --- Demo parent and child (Thomas) ---
        parent = Parent(name="Demo Parent", email="demo@storyspark.dev")
        db.add(parent)
        await db.flush()

        thomas = Child(
            parent_id=parent.id,
            name="Thomas",
            age=4,
            interests=["Legos", "bugs", "dinosaurs", "the garden"],
            favorite_show="Frog & Toad",
        )
        db.add(thomas)

        await db.commit()
        logger.info("Database seeded with Frog & Toad characters, scenarios, and Thomas")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed data
    await seed_data()
    yield


app = FastAPI(
    title="StorySpark",
    description="AI-Powered Character Studio for Parents",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(agent_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "storyspark"}
