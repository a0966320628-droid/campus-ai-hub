from werkzeug.security import generate_password_hash

from extensions import db
from models import (
    ChatMessage, ChatRoom, ChatRoomMember, Community, CommunityMember,
    Department, Friendship, Note, Post, User
)

def seed_data():

    # ========================================================
    # 科系
    # ========================================================

    if (
        Department.query.count()
        == 0
    ):

        db.session.add_all([
            Department(
                code="CS",
                name="資訊工程系"
            ),

            Department(
                code="MIS",
                name="資訊管理系"
            ),

            Department(
                code="EE",
                name="電機工程系"
            )
        ])

        db.session.commit()

    cs_department = (
        Department.query
        .filter_by(
            code="CS"
        )
        .first()
    )

    mis_department = (
        Department.query
        .filter_by(
            code="MIS"
        )
        .first()
    )

    # ========================================================
    # 管理員
    # ========================================================

    admin = (
        User.query
        .filter_by(
            username="admin"
        )
        .first()
    )

    if not admin:

        admin = User(
            full_name=
                "系統管理員",

            username=
                "admin",

            email=
                "admin@example.com",

            birthday=
                "1990-01-01",

            password_hash=
                generate_password_hash(
                    "admin123"
                ),

            role=
                "admin",

            student_no=
                "A0001",

            department_id=(
                cs_department.id
                if cs_department
                else None
            ),

            grade_level=
                "管理者",

            interests=
                "系統管理、校務平台、資料維護",

            bio=
                "我是系統管理員，負責管理貼文與使用者。",

            avatar_url=
                None,

            profile_visibility=
                "public"
        )

        db.session.add(
            admin
        )

        db.session.commit()

    # ========================================================
    # 王小明
    # ========================================================

    user = (
        User.query
        .filter_by(
            username="ming"
        )
        .first()
    )

    if not user:

        user = User(
            full_name=
                "王小明",

            username=
                "ming",

            email=
                "ming@example.com",

            birthday=
                "2004-05-10",

            password_hash=
                generate_password_hash(
                    "user123"
                ),

            role=
                "user",

            student_no=
                "S11223344",

            department_id=(
                cs_department.id
                if cs_department
                else None
            ),

            grade_level=
                "三年級",

            interests=
                "AI、程式設計、資料分析",

            bio=
                "我是資訊工程系學生，喜歡做網頁與 AI 專題。",

            avatar_url=
                None,

            profile_visibility=
                "friends"
        )

        db.session.add(
            user
        )

        db.session.commit()

    # ========================================================
    # 陳小美
    # ========================================================

    user2 = (
        User.query
        .filter_by(
            username="mei"
        )
        .first()
    )

    if not user2:

        user2 = User(
            full_name=
                "陳小美",

            username=
                "mei",

            email=
                "mei@example.com",

            birthday=
                "2005-03-20",

            password_hash=
                generate_password_hash(
                    "user123"
                ),

            role=
                "user",

            student_no=
                "S11223345",

            department_id=(
                mis_department.id
                if mis_department
                else None
            ),

            grade_level=
                "二年級",

            interests=
                "UI 設計、企劃、資料整理",

            bio=
                "我喜歡整理系統流程，也喜歡做介面。",

            avatar_url=
                None,

            profile_visibility=
                "requests"
        )

        db.session.add(
            user2
        )

        db.session.commit()

    # 重新查詢
    admin = (
        User.query
        .filter_by(
            username="admin"
        )
        .first()
    )

    user = (
        User.query
        .filter_by(
            username="ming"
        )
        .first()
    )

    user2 = (
        User.query
        .filter_by(
            username="mei"
        )
        .first()
    )

    # ========================================================
    # 公告
    # ========================================================

    if (
        Post.query.count()
        == 0
        and admin
        and user
    ):

        db.session.add_all([
            Post(
                title=
                    "期中考週圖書館延長開放",

                content=
                    "圖書館本週延長開放到晚上 11 點，"
                    "請同學多加利用。",

                category=
                    "教務",

                is_ai_priority=
                    True,

                author_id=
                    admin.id
            ),

            Post(
                title=
                    "AI 專題競賽開始報名",

                content=
                    "歡迎同學組隊參加，"
                    "系統將依興趣與科系推送。",

                category=
                    "競賽",

                is_ai_priority=
                    True,

                author_id=
                    admin.id
            ),

            Post(
                title=
                    "專題組員招募",

                content=
                    "正在找前端與資料庫同學"
                    "一起完成校園 AI 專題。",

                category=
                    "交流",

                is_ai_priority=
                    False,

                author_id=
                    user.id
            )
        ])

        db.session.commit()

    # ========================================================
    # 筆記
    # ========================================================

    if (
        Note.query.count()
        == 0
        and admin
        and user
    ):

        db.session.add_all([
            Note(
                title=
                    "機器學習課堂筆記",

                content=
                    "今天整理了分類模型、"
                    "訓練流程與評估方法。",

                category=
                    "課堂筆記",

                owner_id=
                    user.id
            ),

            Note(
                title=
                    "系統分析會議摘要",

                content=
                    "確認登入分流、"
                    "貼文權限與管理後台需求。",

                category=
                    "會議紀錄",

                owner_id=
                    admin.id
            )
        ])

        db.session.commit()

    # ========================================================
    # 好友
    # ========================================================

    if (
        Friendship.query.count()
        == 0
        and user
        and user2
    ):

        friendship = (
            Friendship(
                requester_id=
                    user.id,

                addressee_id=
                    user2.id,

                status=
                    "accepted"
            )
        )

        db.session.add(
            friendship
        )

        db.session.commit()

    # ========================================================
    # 私人聊天室
    # ========================================================

    if (
        ChatRoom.query
        .filter_by(
            room_type="private"
        )
        .count()
        == 0
        and user
        and user2
    ):

        private_room = (
            ChatRoom(
                name=
                    "好友私聊",

                topic=
                    "王小明與陳小美的私人聊天",

                room_type=
                    "private",

                require_approval=
                    False,

                created_by=
                    user.id
            )
        )

        db.session.add(
            private_room
        )

        db.session.commit()

        db.session.add_all([
            ChatRoomMember(
                room_id=
                    private_room.id,

                user_id=
                    user.id,

                role=
                    "owner"
            ),

            ChatRoomMember(
                room_id=
                    private_room.id,

                user_id=
                    user2.id,

                role=
                    "member"
            )
        ])

        db.session.commit()

        db.session.add_all([
            ChatMessage(
                room_id=
                    private_room.id,

                sender_id=
                    user.id,

                message_type=
                    "text",

                content=
                    "嗨，你好！"
            ),

            ChatMessage(
                room_id=
                    private_room.id,

                sender_id=
                    user2.id,

                message_type=
                    "text",

                content=
                    "你好，我們來討論專題吧。"
            )
        ])

        db.session.commit()

    # ========================================================
    # 社團
    # ========================================================

    if (
        Community.query.count()
        == 0
        and admin
        and user
    ):

        ai_club = Community(
            name=
                "AI 黑客松研究社",

            description=
                "討論人工智慧、程式競賽與專題實作。",

            community_type=
                "club",

            join_mode=
                "approval",

            join_password_hash=
                None,

            avatar_url=
                None,

            creator_id=
                admin.id
        )

        project_group = (
            Community(
                name=
                    "校園系統專題群組",

                description=
                    "校園 AI 學生資訊交換系統開發討論。",

                community_type=
                    "group",

                join_mode=
                    "open",

                join_password_hash=
                    None,

                avatar_url=
                    None,

                creator_id=
                    user.id
            )
        )

        db.session.add_all([
            ai_club,
            project_group
        ])

        db.session.commit()

        db.session.add_all([
            CommunityMember(
                community_id=
                    ai_club.id,

                user_id=
                    admin.id,

                role=
                    "owner"
            ),

            CommunityMember(
                community_id=
                    project_group.id,

                user_id=
                    user.id,

                role=
                    "owner"
            )
        ])

        db.session.commit()
