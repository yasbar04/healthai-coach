import React, { useState } from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { Post, socialApi } from '../api/social';
import { useAuth } from '../context/AuthContext';

interface Props {
  post: Post;
  currentUserId?: number;
  onLike: (postId: number, liked: boolean, count: number) => void;
  onDelete: (postId: number) => void;
  onCommentPress: (postId: number) => void;
}

export default function PostCard({ post, currentUserId, onLike, onDelete, onCommentPress }: Props) {
  const [liking, setLiking] = useState(false);

  const handleLike = async () => {
    if (liking) return;
    setLiking(true);
    try {
      const res = await socialApi.toggleLike(post.id);
      onLike(post.id, res.liked, res.likes_count);
    } catch {
      // ignore
    } finally {
      setLiking(false);
    }
  };

  const handleDelete = () => {
    Alert.alert('Supprimer', 'Voulez-vous supprimer ce post ?', [
      { text: 'Annuler', style: 'cancel' },
      {
        text: 'Supprimer',
        style: 'destructive',
        onPress: async () => {
          try {
            await socialApi.deletePost(post.id);
            onDelete(post.id);
          } catch {
            Alert.alert('Erreur', 'Impossible de supprimer ce post.');
          }
        },
      },
    ]);
  };

  const avatarUrl = socialApi.getImageUrl(post.author.avatar_url);
  const imageUrl = socialApi.getImageUrl(post.image_url);
  const isOwner = currentUserId === post.author.id;
  const date = new Date(post.created_at).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.avatarContainer}>
          {avatarUrl ? (
            <Image source={{ uri: avatarUrl }} style={styles.avatar} />
          ) : (
            <View style={[styles.avatar, styles.avatarFallback]}>
              <Text style={styles.avatarText}>
                {post.author.display_name.charAt(0).toUpperCase()}
              </Text>
            </View>
          )}
        </View>
        <View style={styles.headerText}>
          <Text style={styles.authorName}>{post.author.display_name}</Text>
          <Text style={styles.date}>{date}</Text>
        </View>
        {isOwner && (
          <TouchableOpacity onPress={handleDelete} style={styles.deleteBtn}>
            <Text style={styles.deleteBtnText}>✕</Text>
          </TouchableOpacity>
        )}
      </View>

      <Text style={styles.content}>{post.content}</Text>

      {imageUrl && (
        <Image source={{ uri: imageUrl }} style={styles.postImage} resizeMode="cover" />
      )}

      <View style={styles.actions}>
        <TouchableOpacity style={styles.actionBtn} onPress={handleLike} disabled={liking}>
          <Text style={styles.actionIcon}>{post.user_liked ? '❤️' : '🤍'}</Text>
          <Text style={styles.actionCount}>{post.likes_count}</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionBtn} onPress={() => onCommentPress(post.id)}>
          <Text style={styles.actionIcon}>💬</Text>
          <Text style={styles.actionCount}>{post.comments_count}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginHorizontal: 16,
    marginBottom: 12,
    padding: 14,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  avatarContainer: { marginRight: 10 },
  avatar: { width: 40, height: 40, borderRadius: 20 },
  avatarFallback: { backgroundColor: '#4F46E5', justifyContent: 'center', alignItems: 'center' },
  avatarText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  headerText: { flex: 1 },
  authorName: { fontWeight: '600', fontSize: 15, color: '#111827' },
  date: { fontSize: 12, color: '#9CA3AF', marginTop: 1 },
  deleteBtn: { padding: 4 },
  deleteBtnText: { color: '#EF4444', fontSize: 16 },
  content: { fontSize: 15, color: '#374151', lineHeight: 22, marginBottom: 10 },
  postImage: {
    width: '100%',
    height: 220,
    borderRadius: 8,
    marginBottom: 10,
  },
  actions: { flexDirection: 'row', gap: 16 },
  actionBtn: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  actionIcon: { fontSize: 18 },
  actionCount: { fontSize: 14, color: '#6B7280' },
});
