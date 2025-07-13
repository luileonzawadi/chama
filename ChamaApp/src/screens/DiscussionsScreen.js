import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {chamaAPI} from '../services/api';

export default function DiscussionsScreen() {
  const [discussions, setDiscussions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDiscussions = async () => {
    try {
      const response = await chamaAPI.getDiscussions();
      setDiscussions(response.discussions || []);
    } catch (error) {
      console.error('Discussions fetch failed:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDiscussions();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchDiscussions();
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <Text>Loading discussions...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }>
      <View style={styles.header}>
        <Icon name="forum" size={48} color="#17a2b8" />
        <Text style={styles.title}>Community Discussions</Text>
        <Text style={styles.subtitle}>Connect with your chama members</Text>
      </View>

      {discussions.length > 0 ? (
        discussions.map((discussion, index) => (
          <TouchableOpacity key={index} style={styles.discussionCard}>
            <View style={styles.discussionHeader}>
              <View style={styles.avatar}>
                <Icon name="person" size={20} color="white" />
              </View>
              <View style={styles.discussionMeta}>
                <Text style={styles.author}>{discussion.author}</Text>
                <Text style={styles.date}>
                  {new Date(discussion.date).toLocaleDateString()}
                </Text>
              </View>
            </View>

            <Text style={styles.discussionTitle}>{discussion.title}</Text>
            <Text style={styles.discussionContent} numberOfLines={3}>
              {discussion.content}
            </Text>

            <View style={styles.discussionFooter}>
              <View style={styles.engagement}>
                <Icon name="comment" size={16} color="#6c757d" />
                <Text style={styles.engagementText}>Join Discussion</Text>
              </View>
              <Icon name="arrow-forward" size={16} color="#007bff" />
            </View>
          </TouchableOpacity>
        ))
      ) : (
        <View style={styles.emptyContainer}>
          <Icon name="forum" size={64} color="#dee2e6" />
          <Text style={styles.emptyTitle}>No Discussions Yet</Text>
          <Text style={styles.emptyText}>
            Be the first to start a conversation with your chama community!
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    backgroundColor: 'white',
    alignItems: 'center',
    padding: 30,
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 15,
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 16,
    color: '#6c757d',
    textAlign: 'center',
  },
  discussionCard: {
    backgroundColor: 'white',
    margin: 15,
    borderRadius: 8,
    padding: 20,
    elevation: 2,
  },
  discussionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#007bff',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  discussionMeta: {
    flex: 1,
  },
  author: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  date: {
    fontSize: 12,
    color: '#6c757d',
    marginTop: 2,
  },
  discussionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  discussionContent: {
    fontSize: 14,
    color: '#6c757d',
    lineHeight: 20,
    marginBottom: 15,
  },
  discussionFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#f1f1f1',
    paddingTop: 15,
  },
  engagement: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  engagementText: {
    fontSize: 14,
    color: '#6c757d',
    marginLeft: 5,
  },
  emptyContainer: {
    alignItems: 'center',
    padding: 40,
    marginTop: 50,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#6c757d',
    marginTop: 20,
    marginBottom: 10,
  },
  emptyText: {
    fontSize: 16,
    color: '#6c757d',
    textAlign: 'center',
  },
});