from pymongo import MongoClient
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.utils.dateparse import parse_date
import uuid
import os


# MongoDB 클라이언트 설정을 위한 함수
def get_mongo_collection(db_name='team4qna', collection_name='qna'):
    # 환경변수에서 MongoDB 서버의 IP 주소와 포트 번호 읽기
    mongo_ip = os.getenv('MONGO_IP', 'localhost')  # 기본값은 'localhost'
    mongo_port = os.getenv('MONGO_PORT', '27017')  # 기본값은 '27017'
    db_name = os.getenv('MONGO_DB_NAME', 'team4qna')  # 기본값은 'team4qna'
    collection_name = os.getenv('MONGO_COLLECTION_NAME', 'qna')  # 기본값은 'qna'
    
    
    # 포트 번호는 정수로 변환
    mongo_port = int(mongo_port)
    
    # MongoDB 클라이언트 설정
    client = MongoClient(mongo_ip, mongo_port)
    db = client[db_name]
    collection = db[collection_name]
    return collection


##질문 추가
class QuestionCreateAPIView(APIView):
    def post(self, request):
        # 필수 필드 확인
        title = request.data.get("title")
        author_nickname = request.data.get("author_nickname")
        date_str = request.data.get("date")  # 사용자가 제공한 날짜

        # 필수 필드 검증
        if not title or not author_nickname or not date_str:
            return Response({"error": "제목, 작성자 닉네임, 날짜는 필수 항목입니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 날짜 형식 검증
        date = parse_date(date_str)
        if not date:
            return Response({"error": "날짜 형식이 잘못되었습니다. YYYY-MM-DD 형식을 사용해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        # 함수 호출로 MongoDB 클라이언트 설정
        questions_collection = get_mongo_collection()

        # 새 질문 데이터 생성
        new_question = {
            "question_id": str(uuid.uuid4()),  # 고유한 질문 ID
            "title": title,  # 사용자가 제공한 질문 제목
            "author_nickname": author_nickname,  # 사용자가 제공한 닉네임
            "created_at": timezone.now(),  # 현재의 날짜와 시간
            "upvotes": 0,  # upvotes 초기값 설정
            "answers": []  # 빈 답변 리스트
        }

        # 사용자가 지정한 날짜의 문서에 새 질문 추가 또는 새 문서 생성
        result = questions_collection.update_one(
            {"date": date_str},
            {"$push": {"questions": new_question}},
            upsert=True  # 문서가 없으면 새로 생성
        )

        # 성공적으로 질문을 추가한 경우
        if result.modified_count or result.upserted_id:
            return Response(new_question, status=status.HTTP_201_CREATED)
        else:
            # 기타 오류 발생 시
            return Response({"error": "질문을 추가하지 못했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

##답변 추가
class AnswerCreateAPIView(APIView):
    def post(self, request):
        # 요청 데이터에서 필요한 정보 추출
        date_str = request.data.get("date")
        question_id = request.data.get("question_id")
        content = request.data.get("content")
        author_nickname = request.data.get("author_nickname")

        # 필수 필드 검증
        if not date_str or not question_id or not content or not author_nickname:
            return Response({"error": "날짜, 질문 ID, 내용, 작성자 닉네임은 필수 항목입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 함수 호출로 MongoDB 클라이언트 설정
        questions_collection = get_mongo_collection()

        # 새 답변 데이터 생성
        new_answer = {
            "answer_id": str(uuid.uuid4()),
            "author_nickname": author_nickname,
            "content": content,
            "created_at": timezone.now(),
            "upvotes": 0
        }

        # date와 question_id가 일치하는 질문을 찾아 답변 추가
        result = questions_collection.update_one(
            {"date": date_str, "questions.question_id": question_id},
            {"$push": {"questions.$.answers": new_answer}}
        )

        # 성공적으로 답변을 추가한 경우
        if result.modified_count:
            return Response(new_answer, status=status.HTTP_201_CREATED)
        else:
            # 질문을 찾지 못하거나 기타 오류 발생 시
            return Response({"error": "답변을 추가하지 못했습니다."}, status=status.HTTP_404_NOT_FOUND)



##특정 날짜 데이터 가져오기
class QuestionsRetrieveAPIView(APIView):
    def get(self, request):
        # 요청 쿼리 파라미터에서 날짜 추출
        date_str = request.query_params.get("date")

        # 날짜 필드 검증
        if not date_str:
            return Response({"error": "날짜는 필수 항목입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 함수 호출로 MongoDB 클라이언트 설정
        questions_collection = get_mongo_collection()

        # 지정된 날짜에 해당하는 문서 조회
        document = questions_collection.find_one({"date": date_str})

        # 문서가 존재하는 경우, 문서 데이터 반환
        if document:
            # MongoDB의 _id 필드 제거
            document.pop("_id", None)
            return Response(document, status=status.HTTP_200_OK)
        else:
            # 해당 날짜의 문서를 찾지 못한 경우, 비어 있는 questions 배열을 포함해 반환
            empty_response = {
                "date": date_str,
                "questions": []
            }
            return Response(empty_response, status=status.HTTP_200_OK)
        

# 질문에 투표를 증가시키는 view 함수
class QuestionVoteAPIView(APIView):
    def post(self, request):
        # 요청 데이터에서 필요한 정보 추출
        date_str = request.data.get("date")
        question_id = request.data.get("question_id")

        # 필수 필드 검증
        if not date_str or not question_id:
            return Response({"error": "날짜와 질문 ID는 필수 항목입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # MongoDB 클라이언트 설정
        questions_collection = get_mongo_collection()

        # 특정 날짜와 질문 ID를 가진 문서를 찾습니다.
        document = questions_collection.find_one({"date": date_str, "questions.question_id": question_id})

        # 문서가 존재하는지 확인합니다.
        if document:
            # 문서 내에서 질문을 찾습니다.
            questions = document.get("questions")
            target_question = None
            for q in questions:
                if q.get("question_id") == question_id:
                    target_question = q
                    break

            # 찾은 질문이 있으면 upvotes를 증가시킵니다.
            if target_question:
                # 현재 upvotes 수를 가져와 1을 증가시킵니다.
                current_upvotes = target_question.get("upvotes", 0)
                target_question["upvotes"] = current_upvotes + 1

                # MongoDB에 업데이트합니다.
                questions_collection.update_one(
                    {"date": date_str, "questions.question_id": question_id},
                    {"$set": {"questions.$": target_question}}
                )

                return Response({"success": "투표가 성공적으로 증가했습니다."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "해당 질문을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "해당 날짜의 문서를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        
class AnswerVoteAPIView(APIView):
    def post(self, request):
        # 요청 데이터에서 필요한 정보 추출
        date_str = request.data.get("date")
        question_id = request.data.get("question_id")
        answer_id = request.data.get("answer_id")

        # 필수 필드 검증
        if not date_str or not question_id or not answer_id:
            return Response({"error": "날짜, 질문 ID, 답변 ID는 필수 항목입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # MongoDB 클라이언트 설정
        questions_collection = get_mongo_collection()

        # 특정 날짜, 질문 ID 및 답변 ID를 가진 문서를 찾습니다.
        document = questions_collection.find_one({"date": date_str, "questions.question_id": question_id})

        # 문서가 존재하는지 확인합니다.
        if document:
            # 문서 내에서 질문과 답변을 찾습니다.
            questions = document.get("questions")
            target_question = None
            target_answer = None

            for q in questions:
                if q.get("question_id") == question_id:
                    target_question = q
                    # 답변을 찾습니다.
                    answers = q.get("answers")
                    for ans in answers:
                        if ans.get("answer_id") == answer_id:
                            target_answer = ans
                            break
                    break

            # 찾은 질문과 답변이 있으면 upvotes를 증가시킵니다.
            if target_question and target_answer:
                # 현재 upvotes 수를 가져와 1을 증가시킵니다.
                current_upvotes = target_answer.get("upvotes", 0)
                target_answer["upvotes"] = current_upvotes + 1

                # MongoDB에 업데이트합니다.
                questions_collection.update_one(
                    {"date": date_str, "questions.question_id": question_id, "questions.answers.answer_id": answer_id},
                    {"$set": {"questions.$[].answers.$[ans].upvotes": target_answer["upvotes"]}},
                    array_filters=[{"ans.answer_id": answer_id}]
                )

                return Response({"success": "투표가 성공적으로 증가했습니다."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "해당 질문 또는 답변을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "해당 날짜의 문서를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)