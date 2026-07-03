import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  FlatList,
  StyleSheet,
  RefreshControl,
  Text,
  ActivityIndicator,
} from 'react-native';
import { Post, socialApi } from '../api/social';
import PostCard from '../components/PostCard';
import CommentModal from '../components/CommentModal';

export default function FeedScreen() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [commentPostId, setCommentPostId] = useState<number | null>(null);
  const [currentUserId, setCurrentUserId] = useState<number | undefined>();

  const fetchPosts = useCallback(async () => {
    try {
      const data = await socialApi.getFeed();
      setPosts(data);
      if (data.length > 0 && !currentUserId) {
        const profile = await socialApi.getProfile();
        setCurrentUserId(profile.id);
      }
    } catch {
      // ignore
    }
  }, [currentUserId]);

  useEffect(() => {
    fetchPosts().finally(() => setLoading(false));
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchPosts();
    setRefreshing(false);
  };

  const handleLike = (postId: number, liked: boolean, count: number) => {
    setPosts((prev) =>
      prev.map((p) =>
        p.id === postId ? { ...p, user_liked: liked, likes_count: count } : p
      )
    );
  };

  const handleDelete = (postId: number) => {
    setPosts((prev) => prev.filter((p) => p.id !== postId));
  };

  const handleCommentCountChange = (postId: number, count: number) => {
    setPosts((prev) =>
      prev.map((p) => (p.id === postId ? { ...p, comments_count: count } : p))
    );
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#4F46E5" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>💪 Fil d'actualité</Text>
      </View>

      <FlatList
        data={posts}
        keyExtractor={(p) => String(p.id)}
        renderItem={({ item }) => (
          <PostCard
            post={item}
            currentUserId={currentUserId}
            onLike={handleLike}
            onDelete={handleDelete}
            onCommentPress={(id) => setCommentPostId(id)}
          />
        )}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={{ paddingVertical: 12 }}
        ListEmptyComponent={
          <View style={styles.centered}>
            <Text style={styles.emptyText}>Aucune publication pour l'instant.</Text>
            <Text style={styles.emptySubtext}>Soyez le premier à publier !</Text>
          </View>
        }
      />

      <CommentModal
        postId={commentPostId}
        currentUserId={currentUserId}
        onClose={() => setCommentPostId(null)}
        onCountChange={handleCommentCountChange}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F3F4F6' },
  header: {
    paddingTop: 56,
    paddingBottom: 12,
    paddingHorizontal: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: { fontSize: 20, fontWeight: '700', color: '#4F46E5' },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingTop: 80 },
  emptyText: { fontSize: 16, fontWeight: '600', color: '#374151', marginBottom: 4 },
  emptySubtext: { fontSize: 14, color: '#9CA3AF' },
});
