from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models import Community, CommunityJoinRequest, CommunityMember


VALID_TYPES = {"group", "club", "forum"}
PASSWORD_MODES = {"password", "password_approval"}
APPROVAL_MODES = {"approval", "password_approval"}


def find_communities(keyword="", filter_type="all"):
    query = Community.query

    if keyword:
        query = query.filter(
            db.or_(
                Community.name.contains(keyword),
                Community.description.contains(keyword)
            )
        )

    if filter_type in VALID_TYPES:
        query = query.filter_by(community_type=filter_type)

    return query.order_by(Community.created_at.desc()).all()


def get_joined_community_ids(user_id):
    return {
        member.community_id
        for member in CommunityMember.query
        .filter_by(user_id=user_id)
        .all()
    }


def create_community_for_user(
    user_id,
    name,
    description="",
    community_type="group",
    join_mode="open",
    password=""
):
    if not name:
        raise ValueError("名稱必填")

    if join_mode in PASSWORD_MODES and not password:
        raise ValueError("此加入方式需要設定密碼")

    community = Community(
        name=name,
        description=description,
        community_type=community_type,
        join_mode=join_mode,
        join_password_hash=(
            generate_password_hash(password)
            if password else None
        ),
        creator_id=user_id
    )

    db.session.add(community)
    db.session.flush()

    db.session.add(
        CommunityMember(
            community_id=community.id,
            user_id=user_id,
            role="owner"
        )
    )
    db.session.commit()

    return community


def join_community_for_user(community, user_id, password=""):
    existing = CommunityMember.query.filter_by(
        community_id=community.id,
        user_id=user_id
    ).first()

    if existing:
        return "already_joined"

    if community.join_mode in PASSWORD_MODES:
        if (
            not password
            or not community.join_password_hash
            or not check_password_hash(
                community.join_password_hash,
                password
            )
        ):
            return "wrong_password"

    if community.join_mode in APPROVAL_MODES:
        old_request = CommunityJoinRequest.query.filter_by(
            community_id=community.id,
            user_id=user_id,
            status="pending"
        ).first()

        if old_request:
            return "already_requested"

        db.session.add(
            CommunityJoinRequest(
                community_id=community.id,
                user_id=user_id,
                status="pending"
            )
        )
        db.session.commit()
        return "requested"

    db.session.add(
        CommunityMember(
            community_id=community.id,
            user_id=user_id,
            role="member"
        )
    )
    db.session.commit()

    return "joined"
