from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from students.models import Student, Class

class SectionRebalanceSuggestion(models.Model):
    """
    Persists AI-suggested student movements to balance class sections.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    current_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='current_suggestions')
    suggested_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='incoming_suggestions')
    
    reasoning = models.TextField(help_text="Explanation for why this move balances the sections.")
    
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ], default='Pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Move {self.student.roll_number} to {self.suggested_class.section}"