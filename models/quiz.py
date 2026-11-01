from sqlalchemy import CheckConstraint, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from database.engine import Base


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    __table_args__ = (
        CheckConstraint("correct_option BETWEEN 1 AND 4", name="ck_quiz_correct_option"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    option_1: Mapped[str] = mapped_column(String(512), nullable=False)
    option_2: Mapped[str] = mapped_column(String(512), nullable=False)
    option_3: Mapped[str] = mapped_column(String(512), nullable=False)
    option_4: Mapped[str] = mapped_column(String(512), nullable=False)
    correct_option: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Общая")
    points: Mapped[int] = mapped_column(
        Integer, default=10, server_default=text("10"), nullable=False
    )

    @property
    def options(self) -> list[str]:
        return [self.option_1, self.option_2, self.option_3, self.option_4]

    def __repr__(self) -> str:
        return f"<QuizQuestion id={self.id} category={self.category!r}>"