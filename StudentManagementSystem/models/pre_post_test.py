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
