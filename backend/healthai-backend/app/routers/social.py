import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..db import SessionLocal
from ..models import User, SocialPost, SocialLike, SocialComment
from .users import current_user

router = APIRouter(prefix="/social", tags=["social"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _author_dict(u: User) -> dict:
    return {
        "id": u.id,
        "display_name": u.display_name or u.email.split("@")[0],
        "avatar_url": u.avatar_url,
    }


def _post_dict(post: SocialPost, user_id: int, db: Session) -> dict:
    likes_count = len(post.likes)
    comments_count = len(post.comments)
    user_liked = any(l.user_id == user_id for l in post.likes)
    return {
        "id": post.id,
        "content": post.content,
        "image_url": post.image_url,
        "created_at": post.created_at.isoformat(),
        "likes_count": likes_count,
        "comments_count": comments_count,
        "user_liked": user_liked,
        "author": _author_dict(post.author),
    }


async def _save_upload(file: UploadFile, prefix: str = "") -> str:
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail="Format image non supporté.")
    filename = f"{prefix}{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    data = await file.read()
    with open(path, "wb") as f:
        f.write(data)
    return f"/uploads/{filename}"


class CommentCreate(BaseModel):
    content: str


@router.get("/feed")
def get_feed(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    posts = (
        db.query(SocialPost)
        .order_by(desc(SocialPost.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_post_dict(p, user.id, db) for p in posts]


@router.post("/posts", status_code=201)
async def create_post(
    content: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    image_url = None
    if image and image.filename:
        image_url = await _save_upload(image)
    post = SocialPost(user_id=user.id, content=content.strip(), image_url=image_url)
    db.add(post)
    db.commit()
    db.refresh(post)
    return _post_dict(post, user.id, db)


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post introuvable.")
    if post.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Non autorisé.")
    db.delete(post)
    db.commit()


@router.post("/posts/{post_id}/like")
def toggle_like(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post introuvable.")
    existing = next((l for l in post.likes if l.user_id == user.id), None)
    if existing:
        db.delete(existing)
        db.commit()
        db.refresh(post)
        return {"liked": False, "likes_count": len(post.likes)}
    like = SocialLike(post_id=post_id, user_id=user.id)
    db.add(like)
    db.commit()
    db.refresh(post)
    return {"liked": True, "likes_count": len(post.likes)}


@router.get("/posts/{post_id}/comments")
def get_comments(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post introuvable.")
    return [
        {
            "id": c.id,
            "content": c.content,
            "created_at": c.created_at.isoformat(),
            "author": _author_dict(c.author),
        }
        for c in sorted(post.comments, key=lambda x: x.created_at)
    ]


@router.post("/posts/{post_id}/comments", status_code=201)
def add_comment(
    post_id: int,
    body: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post introuvable.")
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Contenu vide.")
    comment = SocialComment(post_id=post_id, user_id=user.id, content=body.content.strip())
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {
        "id": comment.id,
        "content": comment.content,
        "created_at": comment.created_at.isoformat(),
        "author": _author_dict(comment.author),
    }


@router.delete("/posts/{post_id}/comments/{comment_id}", status_code=204)
def delete_comment(
    post_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    comment = (
        db.query(SocialComment)
        .filter(SocialComment.id == comment_id, SocialComment.post_id == post_id)
        .first()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Commentaire introuvable.")
    if comment.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Non autorisé.")
    db.delete(comment)
    db.commit()


@router.get("/profile")
def get_profile(user: User = Depends(current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name or user.email.split("@")[0],
        "avatar_url": user.avatar_url,
        "plan": user.plan,
    }


@router.put("/profile")
async def update_profile(
    display_name: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if display_name is not None:
        user.display_name = display_name.strip() or None
    if avatar and avatar.filename:
        user.avatar_url = await _save_upload(avatar, prefix=f"avatar_{user.id}_")
    db.commit()
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name or user.email.split("@")[0],
        "avatar_url": user.avatar_url,
    }
