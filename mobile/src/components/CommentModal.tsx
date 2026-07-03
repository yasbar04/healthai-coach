import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Comment, socialApi } from '../api/social';

interface Props {
  postId: number | null;
  currentUserId?: number;
  onClose: () => void;
  onCountChange: (postId: number, count: number) => void;
}

export default function CommentModal({ postId, currentUserId, onClose, onCountChange }: Props) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (postId === null) return;
    setLoading(true);
    socialApi.getComments(postId).then((data) => {
      setComments(data);
      setLoading(false);
    });
  }, [postId]);

  const handleSend = async () => {
    if (!text.trim() || postId === null) return;
    setSending(true);
    try {
      const comment = await socialApi.addComment(postId, text.trim());
      const updated = [...comments, comment];
      setComments(updated);
      onCountChange(postId, updated.length);
      setText('');
    } catch {
      Alert.alert('Erreur', 'Impossible d\'envoyer le commentaire.');
    } finally {
      setSending(false);
    }
  };

  const handleDelete = async (commentId: number) => {
    if (postId === null) return;
    try {
      await socialApi.deleteComment(postId, commentId);
      const updated = comments.filter((c) => c.id !== commentId);
      setComments(updated);
      onCountChange(postId, updated.length);
    } catch {
      Alert.alert('Erreur', 'Impossible de supprimer ce commentaire.');
    }
  };

  return (
    <Modal visible={postId !== null} animationType="slide" onRequestClose={onClose}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.container}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Commentaires</Text>
          <TouchableOpacity onPress={onClose}>
            <Text style={styles.closeBtn}>✕</Text>
          </TouchableOpacity>
        </View>

        {loading ? (
          <ActivityIndicator style={{ marginTop: 40 }} color="#4F46E5" />
        ) : (
          <FlatList
            data={comments}
            keyExtractor={(c) => String(c.id)}
            contentContainerStyle={{ padding: 16 }}
            ListEmptyComponent={
              <Text style={styles.empty}>Aucun commentaire. Soyez le premier !</Text>
            }
            renderItem={({ item }) => (
              <View style={styles.comment}>
                <View style={styles.commentHeader}>
                  <Text style={styles.commentAuthor}>{item.author.display_name}</Text>
                  <Text style={styles.commentDate}>
                    {new Date(item.created_at).toLocaleDateString('fr-FR')}
                  </Text>
                  {currentUserId === item.author.id && (
                    <TouchableOpacity onPress={() => handleDelete(item.id)}>
                      <Text style={styles.deleteText}>✕</Text>
                    </TouchableOpacity>
                  )}
                </View>
                <Text style={styles.commentContent}>{item.content}</Text>
              </View>
            )}
          />
        )}

        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            placeholder="Écrire un commentaire..."
            placeholderTextColor="#9CA3AF"
            value={text}
            onChangeText={setText}
            multiline
            editable={!sending}
          />
          <TouchableOpacity style={styles.sendBtn} onPress={handleSend} disabled={sending || !text.trim()}>
            {sending ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Text style={styles.sendText}>↑</Text>
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  title: { fontSize: 18, fontWeight: '700', color: '#111827' },
  closeBtn: { fontSize: 20, color: '#6B7280' },
  empty: { textAlign: 'center', color: '#9CA3AF', marginTop: 40, fontSize: 14 },
  comment: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
  },
  commentHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 4, gap: 8 },
  commentAuthor: { fontWeight: '600', color: '#111827', fontSize: 13, flex: 1 },
  commentDate: { fontSize: 11, color: '#9CA3AF' },
  deleteText: { color: '#EF4444', fontSize: 14 },
  commentContent: { fontSize: 14, color: '#374151', lineHeight: 20 },
  inputRow: {
    flexDirection: 'row',
    padding: 12,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    gap: 8,
    alignItems: 'flex-end',
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 14,
    maxHeight: 100,
    color: '#111827',
    backgroundColor: '#F9FAFB',
  },
  sendBtn: {
    backgroundColor: '#4F46E5',
    borderRadius: 20,
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendText: { color: '#fff', fontSize: 18, fontWeight: '700' },
});
