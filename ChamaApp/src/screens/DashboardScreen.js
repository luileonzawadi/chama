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

export default function DashboardScreen() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboard = async () => {
    try {
      const response = await chamaAPI.getDashboard();
      setData(response);
    } catch (error) {
      console.error('Dashboard fetch failed:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchDashboard();
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <Text>Loading...</Text>
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
        <Text style={styles.welcome}>Welcome back!</Text>
        <Text style={styles.memberName}>{data?.member?.name}</Text>
      </View>

      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Icon name="account-balance-wallet" size={24} color="#28a745" />
          <Text style={styles.statValue}>
            KSH {data?.stats?.total_contributions?.toFixed(2) || '0.00'}
          </Text>
          <Text style={styles.statLabel}>Total Contributions</Text>
        </View>
        <View style={styles.statCard}>
          <Icon name="trending-up" size={24} color="#007bff" />
          <Text style={styles.statValue}>
            {data?.stats?.contribution_count || 0}
          </Text>
          <Text style={styles.statLabel}>Contributions Made</Text>
        </View>
        <View style={styles.statCard}>
          <Icon name="account-balance" size={24} color="#ffc107" />
          <Text style={styles.statValue}>{data?.stats?.loan_count || 0}</Text>
          <Text style={styles.statLabel}>Active Loans</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent Contributions</Text>
        {data?.recent_contributions?.length > 0 ? (
          data.recent_contributions.map((contribution, index) => (
            <View key={index} style={styles.listItem}>
              <View>
                <Text style={styles.itemAmount}>
                  KSH {contribution.amount}
                </Text>
                <Text style={styles.itemDescription}>
                  {contribution.description || 'Regular contribution'}
                </Text>
              </View>
              <Text style={styles.itemDate}>
                {new Date(contribution.date).toLocaleDateString()}
              </Text>
            </View>
          ))
        ) : (
          <Text style={styles.emptyText}>No contributions yet</Text>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent Loans</Text>
        {data?.recent_loans?.length > 0 ? (
          data.recent_loans.map((loan, index) => (
            <View key={index} style={styles.listItem}>
              <View>
                <Text style={styles.itemAmount}>KSH {loan.amount}</Text>
                <Text style={styles.itemDescription}>{loan.purpose}</Text>
              </View>
              <View style={styles.statusContainer}>
                <Text
                  style={[
                    styles.status,
                    loan.status === 'Approved' && styles.statusApproved,
                    loan.status === 'Pending' && styles.statusPending,
                    loan.status === 'Rejected' && styles.statusRejected,
                  ]}>
                  {loan.status}
                </Text>
              </View>
            </View>
          ))
        ) : (
          <Text style={styles.emptyText}>No loans yet</Text>
        )}
      </View>
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
    backgroundColor: '#007bff',
    padding: 20,
    paddingTop: 40,
  },
  welcome: {
    color: 'white',
    fontSize: 16,
  },
  memberName: {
    color: 'white',
    fontSize: 24,
    fontWeight: 'bold',
  },
  statsContainer: {
    flexDirection: 'row',
    padding: 15,
    justifyContent: 'space-between',
  },
  statCard: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 15,
    alignItems: 'center',
    flex: 1,
    marginHorizontal: 5,
    elevation: 2,
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 5,
  },
  statLabel: {
    fontSize: 12,
    color: '#6c757d',
    textAlign: 'center',
    marginTop: 5,
  },
  section: {
    backgroundColor: 'white',
    margin: 15,
    borderRadius: 8,
    padding: 15,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  listItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f1f1',
  },
  itemAmount: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#28a745',
  },
  itemDescription: {
    fontSize: 14,
    color: '#6c757d',
  },
  itemDate: {
    fontSize: 12,
    color: '#6c757d',
  },
  statusContainer: {
    alignItems: 'flex-end',
  },
  status: {
    fontSize: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    overflow: 'hidden',
  },
  statusApproved: {
    backgroundColor: '#d4edda',
    color: '#155724',
  },
  statusPending: {
    backgroundColor: '#fff3cd',
    color: '#856404',
  },
  statusRejected: {
    backgroundColor: '#f8d7da',
    color: '#721c24',
  },
  emptyText: {
    textAlign: 'center',
    color: '#6c757d',
    fontStyle: 'italic',
  },
});