# GameProgress/models/pre_post_test.py

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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_test_type_display()}: {self.name}"


class TestQuestion(models.Model):
    MULTIPLE_CHOICE = "mcq"
    CHECKBOX = "checkbox"
    DROPDOWN = "dropdown"
    SHORT = "short"
    PARAGRAPH = "paragraph"
    ENUMERATION = "enum"

    QUESTION_TYPES = [
        (MULTIPLE_CHOICE, "Multiple Choice"),
        (CHECKBOX, "Checkboxes"),
        (DROPDOWN, "Dropdown"),
        (SHORT, "Short Answer"),
        (PARAGRAPH, "Paragraph"),
        (ENUMERATION, "Enumeration"),
    ]

    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
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

    def __str__(self):
        return f"Choice for Q{self.question.id}: {self.text}"


class StudentAnswer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE)
    selected_choices = models.ManyToManyField(TestChoice, blank=True)  # MCQ / Checkbox / Dropdown
    text_answer = models.TextField(blank=True, null=True)  # Short / Paragraph / Enum
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "question")

    def __str__(self):
        return f"{self.student} - {self.question}"

    def check_correctness(self):
        """Auto-check correctness for objective questions"""
        if self.question.question_type in [TestQuestion.MULTIPLE_CHOICE, TestQuestion.CHECKBOX, TestQuestion.DROPDOWN]:
            correct_choices = set(self.question.choices.filter(is_correct=True).values_list("id", flat=True))
            selected = set(self.selected_choices.values_list("id", flat=True))
            self.is_correct = (correct_choices == selected)
        else:
            # For short/paragraph/enum → correctness can be manual or left False by default
            self.is_correct = False
        self.save()
        return self.is_correct


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
        """Calculate score based on student's answers"""
        total_score = 0.0
        max_score = 0.0

        answers = StudentAnswer.objects.filter(student=self.student, question__test=self.test)
        for ans in answers:
            ans.check_correctness()
            if ans.is_correct:
                total_score += ans.question.points
            max_score += ans.question.points

        self.score = total_score
        self.completed = True
        self.save()
        return {"score": total_score, "max_score": max_score}
