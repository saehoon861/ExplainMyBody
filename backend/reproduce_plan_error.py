
import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, init_db
from services.llm.weekly_plan_service import WeeklyPlanService
from schemas.llm import GenerateWeeklyPlanRequest
from repositories.common.health_record_repository import HealthRecordRepository

async def main():
    init_db() # Ensure DB is initialized and migrated
    db = SessionLocal()
    try:
        # 1. Find a user and their latest health record
        # For simplicity, we'll try user_id=1, or find the first user with records
        user_id = 1
        record = HealthRecordRepository.get_latest(db, user_id)
        
        if not record:
            print(f"No health record found for user {user_id}")
            # Try to find any record
            from models.health_record import HealthRecord
            record = db.query(HealthRecord).first()
            if not record:
                print("No health records in DB")
                return
            user_id = record.user_id
            print(f"Found record {record.id} for user {user_id}")
        else:
            print(f"Using latest record {record.id} for user {user_id}")

        # 2. Create the request object
        # The frontend sends:
        # action: "generate"
        # record_id: ...
        # user_goal_type: ...
        # user_goal_description: ...
        # preferences: ...
        # health_specifics: ...

        request_data = GenerateWeeklyPlanRequest(
            action="generate",
            record_id=record.id,
            user_goal_type="다이어트",
            user_goal_description="다이어트, 선호하는 운동: 헬스장(웨이트), 러닝/유산소. 특이사항: 허리 디스크 약간 있음",
            preferences="헬스장(웨이트), 러닝/유산소",
            health_specifics="허리 디스크 약간 있음"
        )
        
        print("Request Data:", request_data)

        # 3. Call the service
        service = WeeklyPlanService()
        
        print("Calling generate_plan...")
        try:
            # Note: The service expects GoalPlanRequest, but we are passing GenerateWeeklyPlanRequest.
            # This is what weekly_plans.py does.
            result = await service.generate_plan(db, user_id, request_data)
            print("Success!")
            print("Plan ID:", result["weekly_plan"].id)
        except Exception as e:
            print("Error occurred:")
            print(e)
            import traceback
            traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
