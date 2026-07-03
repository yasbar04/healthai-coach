import React, { useState, useEffect, useRef } from 'react'
import { socialApi, Post, Comment, imageUrl } from '../api/social'

function Avatar({ author }: { author: { display_name: string; avatar_url: string | null } }) {
  const url = imageUrl(author.avatar_url)
  if (url) return <img src={url} alt="" className="w-9 h-9 rounded-full object-cover" />
  return (
    <div className="w-9 h-9 rounded-full bg-primary-600 flex items-center justify-center text-white font-bold text-sm">
      {author.display_name.charAt(0).toUpperCase()}
    </div>
  )
}

function CommentPanel({
  postId,
  currentUserId,
  onClose,
  onCountChange,
}: {
  postId: number
  currentUserId: number | undefined
  onClose: () => void
  onCountChange: (count: number) => void
}) {
  const [comments, setComments] = useState<Comment[]>([])
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)

  useEffect(() => {
    socialApi.getComments(postId).then(setComments)
  }, [postId])

  const send = async () => {
    if (!text.trim()) return
    setSending(true)
    try {
      const c = await socialApi.addComment(postId, text.trim())
      const updated = [...comments, c]
      setComments(updated)
      onCountChange(updated.length)
      setText('')
    } finally {
      setSending(false)
    }
  }

  const remove = async (commentId: number) => {
    await socialApi.deleteComment(postId, commentId)
    const updated = comments.filter(c => c.id !== commentId)
    setComments(updated)
    onCountChange(updated.length)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="bg-white w-full sm:max-w-lg rounded-t-2xl sm:rounded-2xl shadow-2xl flex flex-col max-h-[80vh]"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <h3 className="font-semibold text-gray-800">Commentaires</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>

        <div className="overflow-y-auto flex-1 p-4 space-y-3">
          {comments.length === 0 && (
            <p className="text-center text-gray-400 text-sm py-6">Aucun commentaire. Soyez le premier !</p>
          )}
          {comments.map(c => (
            <div key={c.id} className="flex gap-2">
              <Avatar author={c.author} />
              <div className="flex-1 bg-gray-50 rounded-xl px-3 py-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-gray-700">{c.author.display_name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">
                      {new Date(c.created_at).toLocaleDateString('fr-FR')}
                    </span>
                    {currentUserId === c.author.id && (
                      <button onClick={() => remove(c.id)} className="text-red-400 hover:text-red-600 text-xs">✕</button>
                    )}
                  </div>
                </div>
                <p className="text-sm text-gray-700 mt-0.5">{c.content}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="p-3 border-t flex gap-2">
          <input
            className="flex-1 border border-gray-200 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400"
            placeholder="Écrire un commentaire..."
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            disabled={sending}
          />
          <button
            onClick={send}
            disabled={sending || !text.trim()}
            className="bg-primary-600 text-white rounded-full w-9 h-9 flex items-center justify-center disabled:opacity-40 hover:bg-primary-700"
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  )
}

function PostCard({
  post,
  currentUserId,
  onLike,
  onDelete,
  onComment,
}: {
  post: Post
  currentUserId: number | undefined
  onLike: (id: number, liked: boolean, count: number) => void
  onDelete: (id: number) => void
  onComment: (id: number) => void
}) {
  const [liking, setLiking] = useState(false)
  const imgUrl = imageUrl(post.image_url)

  const like = async () => {
    if (liking) return
    setLiking(true)
    try {
      const res = await socialApi.toggleLike(post.id)
      onLike(post.id, res.liked, res.likes_count)
    } finally {
      setLiking(false)
    }
  }

  const del = async () => {
    if (!confirm('Supprimer ce post ?')) return
    await socialApi.deletePost(post.id)
    onDelete(post.id)
  }

  const date = new Date(post.created_at).toLocaleDateString('fr-FR', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  })

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="flex items-center gap-3 px-4 pt-4 pb-2">
        <Avatar author={post.author} />
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm text-gray-900 truncate">{post.author.display_name}</p>
          <p className="text-xs text-gray-400">{date}</p>
        </div>
        {currentUserId === post.author.id && (
          <button onClick={del} className="text-gray-300 hover:text-red-500 text-sm px-1">✕</button>
        )}
      </div>

      <p className="px-4 pb-3 text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">{post.content}</p>

      {imgUrl && (
        <img src={imgUrl} alt="" className="w-full max-h-80 object-cover" />
      )}

      <div className="flex items-center gap-4 px-4 py-3 border-t border-gray-50">
        <button
          onClick={like}
          disabled={liking}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-red-500 transition-colors"
        >
          <span className="text-base">{post.user_liked ? '❤️' : '🤍'}</span>
          <span>{post.likes_count}</span>
        </button>
        <button
          onClick={() => onComment(post.id)}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-primary-600 transition-colors"
        >
          <span className="text-base">💬</span>
          <span>{post.comments_count}</span>
        </button>
      </div>
    </div>
  )
}

export default function SocialPage() {
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(true)
  const [currentUserId, setCurrentUserId] = useState<number>()
  const [content, setContent] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [posting, setPosting] = useState(false)
  const [commentPostId, setCommentPostId] = useState<number | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    Promise.all([socialApi.getFeed(), socialApi.getProfile()]).then(([feed, profile]) => {
      setPosts(feed)
      setCurrentUserId(profile.id)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const pickFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }

  const submit = async () => {
    if (!content.trim()) return
    setPosting(true)
    try {
      const post = await socialApi.createPost(content.trim(), file ?? undefined)
      setPosts(prev => [post, ...prev])
      setContent('')
      setFile(null)
      setPreview(null)
      if (fileRef.current) fileRef.current.value = ''
    } finally {
      setPosting(false)
    }
  }

  const handleLike = (id: number, liked: boolean, count: number) =>
    setPosts(p => p.map(post => post.id === id ? { ...post, user_liked: liked, likes_count: count } : post))

  const handleDelete = (id: number) =>
    setPosts(p => p.filter(post => post.id !== id))

  const handleCommentCount = (postId: number, count: number) =>
    setPosts(p => p.map(post => post.id === postId ? { ...post, comments_count: count } : post))

  return (
    <div className="max-w-xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">🌐 Communauté</h1>

      {/* Composer */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 mb-6">
        <textarea
          className="w-full resize-none text-sm text-gray-800 placeholder-gray-400 focus:outline-none min-h-[80px]"
          placeholder="Partagez votre progression, votre séance, une astuce..."
          value={content}
          onChange={e => setContent(e.target.value)}
          disabled={posting}
        />
        {preview && (
          <div className="relative mt-2">
            <img src={preview} alt="" className="rounded-xl max-h-48 object-cover w-full" />
            <button
              onClick={() => { setFile(null); setPreview(null); if (fileRef.current) fileRef.current.value = '' }}
              className="absolute top-2 right-2 bg-black/50 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs"
            >✕</button>
          </div>
        )}
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
          <button
            onClick={() => fileRef.current?.click()}
            className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-primary-600"
          >
            <span>📷</span> Photo
          </button>
          <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={pickFile} />
          <button
            onClick={submit}
            disabled={!content.trim() || posting}
            className="bg-primary-600 text-white text-sm font-semibold px-5 py-2 rounded-full hover:bg-primary-700 disabled:opacity-40"
          >
            {posting ? '...' : 'Publier'}
          </button>
        </div>
      </div>

      {/* Feed */}
      {loading ? (
        <div className="text-center text-gray-400 py-12">Chargement...</div>
      ) : posts.length === 0 ? (
        <div className="text-center text-gray-400 py-12">
          <p className="text-4xl mb-3">💬</p>
          <p className="font-medium">Aucune publication pour l'instant.</p>
          <p className="text-sm mt-1">Soyez le premier à partager !</p>
        </div>
      ) : (
        <div className="space-y-4">
          {posts.map(post => (
            <PostCard
              key={post.id}
              post={post}
              currentUserId={currentUserId}
              onLike={handleLike}
              onDelete={handleDelete}
              onComment={id => setCommentPostId(id)}
            />
          ))}
        </div>
      )}

      {commentPostId !== null && (
        <CommentPanel
          postId={commentPostId}
          currentUserId={currentUserId}
          onClose={() => setCommentPostId(null)}
          onCountChange={count => handleCommentCount(commentPostId, count)}
        />
      )}
    </div>
  )
}
