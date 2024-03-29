from djongo import models

class Question(models.Model):
    date = models.DateField(auto_now_add=True)
    nickname = models.CharField(max_length=100)
    question_id = models.CharField(max_length=100, unique=True)  # 고유 식별자로 설정
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    upvotes = models.IntegerField(default=0)

    class Meta:
        db_table = 'qna'

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    nickname = models.CharField(max_length=100)
    answer_id = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    upvotes = models.IntegerField(default=0)
