from django.urls import path
from .views import QuestionsRetrieveAPIView, AnswerCreateAPIView, QuestionCreateAPIView , QuestionVoteAPIView, AnswerVoteAPIView

urlpatterns = [
    # 질문 검색 API
    path('questions/', QuestionsRetrieveAPIView.as_view(), name='retrieve-questions'),
    
    # 답변 추가 API
    path('addAnswer/', AnswerCreateAPIView.as_view(), name='create-answer'),

    # 질문 추가 API
    path('addQuestion/', QuestionCreateAPIView.as_view(), name='create-question'),

    #question 추천 추가
    path('addQuestionVote/', QuestionVoteAPIView.as_view(), name='add-questionVote'),

    #답변 추천 추가
    path('addAnswerVote/', AnswerVoteAPIView.as_view(), name='add-answerVote'),
]