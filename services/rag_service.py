"""Campus AI Hub: permission-aware multi-feature retrieval (no schema changes)."""
import math
import re
from collections import Counter
from datetime import datetime
from models import (Post, Note, Community, CommunityMember, ChatRoom,
                    ChatRoomMember, Meeting, MeetingParticipant, Friendship, User)

SYNONYMS = {
    '活動': ('競賽', '比賽', '報名', '講座', '研習', '工作坊', '展覽', '社團活動'),
    '比賽': ('競賽', '活動', '報名', '專題'),
    '公告': ('通知', '消息', '資訊', '最新'),
    '筆記': ('課程', '學習', '講義', '複習'),
    '社團': ('群組', '社群', '加入'),
    '聊天': ('聊天室', '群聊', '私聊', '訊息'),
    '會議': ('視訊', '語音', '開會'),
    '朋友': ('好友', '交友'),
    '好友': ('朋友', '邀請'),
    'python': ('程式', '程式設計'),
    '資料庫': ('sql', 'sqlite', 'postgresql', '資料表'),
}
RECENT_TERMS = ('最近', '最新', '近期', '現在', '這週', '本週', '有什麼', '有哪些')

def tokens(text):
    words = re.findall(r'[a-z0-9_]+|[\u3400-\u9fff]+', str(text or '').lower())
    result = []
    for w in words:
        if re.search(r'[\u3400-\u9fff]', w):
            result.extend(w[i:i+2] for i in range(len(w)-1))
            if len(w) == 1: result.append(w)
        else: result.append(w)
    return result

def expand(question):
    terms = [question]
    lower = question.lower()
    for key, alternatives in SYNONYMS.items():
        if key in lower:
            terms.extend(alternatives)
    return terms

def retrieve(question, user_id, limit=8):
    """Only public posts, own notes, memberships and own account metadata.

    Chat/community message bodies, passwords, private profiles and other users' notes
    are intentionally excluded. Membership information is only shown to members.
    """
    uid = int(user_id)
    question = str(question or '').strip()[:1000]
    if not question: return []
    docs = []
    def add(kind, obj_id, title, content='', created=None, priority=False, url=None):
        docs.append(dict(type=kind, id=obj_id, title=str(title or ''),
                         content=str(content or ''), priority=bool(priority),
                         created=created, **({'url':url} if url else {})))

    for p in Post.query.order_by(Post.created_at.desc()).limit(500).all():
        add('post', p.id, p.title, p.content, p.created_at,
            getattr(p, 'is_ai_priority', False), f'/ai/source/post/{p.id}')
    for n in Note.query.filter_by(owner_id=uid).order_by(Note.created_at.desc()).limit(500).all():
        add('note', n.id, n.title, n.content, n.created_at,
            url=f'/ai/source/note/{n.id}')

    # Publicly discoverable community names and descriptions only. Never index messages.
    for c in Community.query.order_by(Community.created_at.desc()).limit(300).all():
        add('community', c.id, c.name, c.description, c.created_at, url='/communities/')

    # Private chat room metadata is accessible only to current members.
    room_ids = [x.room_id for x in ChatRoomMember.query.filter_by(user_id=uid).limit(500).all()]
    if room_ids:
        for room in ChatRoom.query.filter(ChatRoom.id.in_(room_ids)).limit(500).all():
            add('chat_room', room.id, room.name, room.topic, room.created_at, url='/chat')

    # Meeting metadata only if the user created or joined the meeting.
    meeting_ids = {x.meeting_id for x in MeetingParticipant.query.filter_by(user_id=uid).limit(500).all()}
    for meeting in Meeting.query.filter_by(created_by=uid).limit(500).all():
        meeting_ids.add(meeting.id)
    if meeting_ids:
        for meeting in Meeting.query.filter(Meeting.id.in_(meeting_ids)).limit(500).all():
            add('meeting', meeting.id, meeting.title, '', meeting.created_at, url='/meetings/')

    # Only the current user's friendship connections, never arbitrary user profiles.
    friendships = Friendship.query.filter(
        (Friendship.requester_id == uid) | (Friendship.addressee_id == uid)
    ).limit(500).all()
    friend_ids = {f.addressee_id if f.requester_id == uid else f.requester_id
                  for f in friendships if f.status == 'accepted'}
    if friend_ids:
        for friend in User.query.filter(User.id.in_(friend_ids)).limit(500).all():
            add('friend', friend.id, friend.full_name, '已接受的好友', url='/friends')

    # Focus matching on meaningful terms, rather than generic conversational words.
    cleaned = question.lower()
    for filler in ('請幫我', '幫我', '請問', '可以', '一下', '最近', '最新',
                   '近期', '現在', '這週', '本週', '有什麼', '有哪些', '相關的',
                   '相關', '我要', '我想', '請', '找出', '搜尋', '查詢', '整理'):
        cleaned = cleaned.replace(filler, ' ')
    query_terms = expand(cleaned.strip() or question)
    query_tokens = Counter(tokens(' '.join(query_terms)))
    # Prevent common conversational filler from drowning out topical matches.
    for t in ('最近', '有什', '什麼', '哪些', '請問', '幫我', '可以', '一下'):
        query_tokens.pop(t, None)
    if not query_tokens:
        # For recent announcement requests, provide a recent-post shortlist.
        if any(term in question for term in ('公告', '活動', '消息', '競賽')):
            recent = [d for d in docs if d['type'] == 'post']
            recent.sort(key=lambda d: d['created'] or datetime.min, reverse=True)
            return [dict(type=d['type'], id=d['id'], title=d['title'],
                         url=d.get('url'), excerpt=d['content'][:900])
                    for d in recent[:max(1, min(int(limit), 30))]]
        return []
    tokenized = [Counter(tokens(d['title'] + ' ' + d['title'] + ' ' + d['content'])) for d in docs]
    df = Counter()
    for dt in tokenized: df.update(dt.keys())
    scored = []
    for d, dt in zip(docs, tokenized):
        score = sum(min(dt.get(t, 0), 4) * count * math.log(1 + (len(docs)+1)/(df[t]+1))
                    for t, count in query_tokens.items())
        if d['priority'] and score > 0: score *= 1.2
        if score > 0: scored.append((score, d))
    scored.sort(key=lambda x: (x[0], x[1]['created'] or datetime.min), reverse=True)

    # Broad recent-activity questions: show recent announcements if strict search misses.
    if not scored and any(t in question for t in RECENT_TERMS) and any(
        t in question for t in ('活動', '公告', '消息', '資訊', '競賽', '比賽')):
        posts = [d for d in docs if d['type'] == 'post']
        posts.sort(key=lambda d: d['created'] or datetime.min, reverse=True)
        scored = [(0, d) for d in posts[:limit]]

    results = []
    for _, d in scored[:max(1, min(int(limit), 30))]:
        out = {k:v for k,v in d.items() if k not in ('content','created','priority')}
        out['excerpt'] = d['content'][:900]
        results.append(out)
    return results
