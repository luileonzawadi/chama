import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {chamaAPI} from '../services/api';

export default function ActivitiesScreen() {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchActivities = async () => {
    try {
      const response = await chamaAPI.getActivities();
      setActivities(response.activities || []);
    } catch (error) {
      console.error('Activities fetch failed:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchActivities();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchActivities();
  };

  const getActivityIcon = type => {
    switch (type) {
      case 'meeting':
        return 'group';
      case 'event':
        return 'event';
      case 'training':
        return 'school';
      case 'review':
        return 'assessment';
      case 'social':
        return 'celebration';
      default:
        return 'event';
    }
  };

  const getActivityColor = type => {
    switch (type) {
      case 'meeting':
        return '#007bff';
      case 'event':
        return '#28a745';
      case 'training':
        return '#ffc107';
      case 'review':
        return '#dc3545';
      case 'social':
        return '#e83e8c';
      default:
        return '#6c757d';
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <Text>Loading activities...</Text>
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
        <Icon name="event" size={48} color="#28a745" />
        <Text style={styles.title}>Upcoming Activities</Text>
        <Text style={styles.subtitle}>Stay updated with chama events</Text>
      </View>

      {activities.length > 0 ? (
        activities.map((activity, index) => (
          <View key={index} style={styles.activityCard}>
            <View style={styles.activityHeader}>
              <View
                style={[
                  styles.activityIcon,
                  {backgroundColor: getActivityColor(activity.type)},
                ]}>
                <Icon
                  name={getActivityIcon(activity.type)}
                  size={24}
                  color="white"
                />
              </View>
              <View style={styles.activityMeta}>
                <Text style={styles.activityTitle}>{activity.title}</Text>
                <Text style={styles.activityType}>
                  {activity.type.charAt(0).toUpperCase() + activity.type.slice(1)}
                </Text>
              </View>
            </View>

            {activity.description && (
              <Text style={styles.activityDescription}>
                {activity.description}
              </Text>
            )}

            <View style={styles.activityFooter}>
              <View style={styles.dateTime}>
                <Icon name="schedule" size={16} color="#6c757d" />
                <Text style={styles.dateTimeText}>
                  {new Date(activity.date).toLocaleDateString()} at{' '}
                  {new Date(activity.date).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </Text>
              </View>
            </View>
          </View>
        ))
      ) : (
        <View style={styles.emptyContainer}>
          <Icon name="event" size={64} color="#dee2e6" />
          <Text style={styles.emptyTitle}>No Upcoming Activities</Text>
          <Text style={styles.emptyText}>
            Check back later for new events and meetings.
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
  activityCard: {
    backgroundColor: 'white',
    margin: 15,
    borderRadius: 8,
    padding: 20,
    elevation: 2,
  },
  activityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  activityIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 15,
  },
  activityMeta: {
    flex: 1,
  },
  activityTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  activityType: {
    fontSize: 14,
    color: '#6c757d',
    marginTop: 2,
  },
  activityDescription: {
    fontSize: 14,
    color: '#6c757d',
    lineHeight: 20,
    marginBottom: 15,
  },
  activityFooter: {
    borderTopWidth: 1,
    borderTopColor: '#f1f1f1',
    paddingTop: 15,
  },
  dateTime: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dateTimeText: {
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