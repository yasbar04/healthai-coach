import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Image,
  StyleSheet,
  Alert,
  ActivityIndicator,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { socialApi } from '../api/social';

export default function CreatePostScreen() {
  const [content, setContent] = useState('');
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission refusée', 'Accès à la galerie requis.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
    });
    if (!result.canceled) {
      setImageUri(result.assets[0].uri);
    }
  };

  const handleSubmit = async () => {
    if (!content.trim()) {
      Alert.alert('Erreur', 'Le contenu est requis.');
      return;
    }
    setLoading(true);
    try {
      await socialApi.createPost(content.trim(), imageUri ?? undefined);
      setContent('');
      setImageUri(null);
      Alert.alert('Publié !', 'Votre publication a été partagée.');
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? 'Erreur lors de la publication.';
      Alert.alert('Erreur', msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Nouvelle publication</Text>
      </View>

      <ScrollView contentContainerStyle={styles.body}>
        <TextInput
          style={styles.textarea}
          placeholder="Quoi de neuf ? Partagez votre expérience fitness..."
          placeholderTextColor="#9CA3AF"
          value={content}
          onChangeText={setContent}
          multiline
          maxLength={1000}
          editable={!loading}
        />
        <Text style={styles.charCount}>{content.length}/1000</Text>

        {imageUri && (
          <View style={styles.imagePreview}>
            <Image source={{ uri: imageUri }} style={styles.previewImg} resizeMode="cover" />
            <TouchableOpacity style={styles.removeImage} onPress={() => setImageUri(null)}>
              <Text style={styles.removeImageText}>✕</Text>
            </TouchableOpacity>
          </View>
        )}

        <TouchableOpacity style={styles.imageBtn} onPress={pickImage} disabled={loading}>
          <Text style={styles.imageBtnText}>📷  Ajouter une photo</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.submitBtn, (!content.trim() || loading) && styles.submitBtnDisabled]}
          onPress={handleSubmit}
          disabled={!content.trim() || loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.submitText}>Publier</Text>
          )}
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
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
  headerTitle: { fontSize: 20, fontWeight: '700', color: '#111827' },
  body: { padding: 16 },
  textarea: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    fontSize: 15,
    color: '#111827',
    minHeight: 120,
    textAlignVertical: 'top',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    marginBottom: 4,
  },
  charCount: { fontSize: 12, color: '#9CA3AF', textAlign: 'right', marginBottom: 12 },
  imagePreview: { position: 'relative', marginBottom: 12 },
  previewImg: { width: '100%', height: 200, borderRadius: 10 },
  removeImage: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'rgba(0,0,0,0.55)',
    borderRadius: 14,
    width: 28,
    height: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeImageText: { color: '#fff', fontSize: 14, fontWeight: '700' },
  imageBtn: {
    borderWidth: 1.5,
    borderColor: '#4F46E5',
    borderRadius: 10,
    borderStyle: 'dashed',
    padding: 14,
    alignItems: 'center',
    marginBottom: 16,
  },
  imageBtnText: { color: '#4F46E5', fontSize: 15 },
  submitBtn: {
    backgroundColor: '#4F46E5',
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
  },
  submitBtnDisabled: { opacity: 0.5 },
  submitText: { color: '#fff', fontWeight: '700', fontSize: 16 },
});
