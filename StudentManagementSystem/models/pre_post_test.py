from django.db import models
from StudentManagementSystem.models.student import Student


class TestDefinition(models.Model):
    PRE = "pre"
    POST = "post"
    TEST_TYPE_CHOICES = [
        (PRE, "Pre-Test"),
        (POST, "Post-Test"),
    ]

    name = models.CharField(max_length=150)
    test_type = models.CharField(max_length=10, choices=TEST_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    shuffle_questions = models.BooleanField(default=False)
    shuffle_choices = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_test_type_display()}: {self.name}"


class TestQuestion(models.Model):
    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    points = models.FloatField(default=1.0)
    required = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.test.name} - Q{self.sort_order}: {self.text[:40]}"


class TestChoice(models.Model):
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)  # NEW FIELD

    class Meta:
        ordering = ["sort_order", "id"]  # ensure stable order

    def __str__(self):
        return f"Choice for Q{self.question.id}: {self.text}"


class StudentAnswer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE)
    choice = models.ForeignKey(TestChoice, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "question")

    def __str__(self):
        return f"{self.student} - {self.question}"

    def save(self, *args, **kwargs):
        # ✅ correctness auto-check for MCQ
        self.is_correct = self.choice.is_correct
        super().save(*args, **kwargs)


class StudentTest(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE)
    score = models.FloatField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "test")

    def __str__(self):
        return f"{self.student} - {self.test.name} ({self.score})"

    def grade_test(self):
        answers = StudentAnswer.objects.filter(student=self.student, question__test=self.test)

        total_score = sum(ans.question.points for ans in answers)
        score = sum(ans.question.points for ans in answers if ans.is_correct)

        self.score = score
        self.completed = True
        self.save()

        return {"score": score, "max_score": total_score}

class StudentProgress(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE)

    current_page = models.PositiveIntegerField(default=0)
    page_size = models.PositiveIntegerField(default=25)  # default like Google Forms

    question_order = models.JSONField(default=list)   # [5, 2, 7, 1...]
    choice_orders = models.JSONField(default=dict)    # {"5": [12,13,14]}

    answers = models.JSONField(default=dict)          # {"5": 14, "2": 22}
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "test")

    def init_order(self):
        if not self.question_order:
            questions = list(self.test.questions.values_list("id", flat=True))
            if self.test.shuffle_questions:
                import random
                random.shuffle(questions)
            self.question_order = list(questions)

            choice_map = {}
            for qid in questions:
                q = TestQuestion.objects.get(id=qid)
                choices = list(q.choices.values_list("id", flat=True))
                if self.test.shuffle_choices:
                    import random
                    random.shuffle(choices)
                choice_map[str(qid)] = list(choices)
            self.choice_orders = choice_map
            self.save(update_fields=["question_order", "choice_orders"])

    def get_page_questions(self):
        """Return questions for current page"""
        start = self.current_page * self.page_size
        end = start + self.page_size
        qids = self.question_order[start:end]
        return list(TestQuestion.objects.filter(id__in=qids).order_by(
            models.Case(*[models.When(id=qid, then=pos) for pos, qid in enumerate(qids)])
        ))

    def get_choices_for_question(self, question):
        """Return ordered choices for a given question"""
        choice_ids = self.choice_orders.get(str(question.id), [])
        return list(TestChoice.objects.filter(id__in=choice_ids).order_by(
            models.Case(*[models.When(id=cid, then=pos) for pos, cid in enumerate(choice_ids)])
        ))

    def next_page(self):
        self.current_page += 1
        self.save(update_fields=["current_page"])
        return self.get_page_questions()
