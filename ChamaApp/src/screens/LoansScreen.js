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

export default function LoansScreen() {
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchLoans = async () => {
    try {
      const response = await chamaAPI.getLoans();
      setLoans(response.loans || []);
    } catch (error) {
      console.error('Loans fetch failed:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchLoans();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchLoans();
  };

  const getStatusIcon = status => {
    switch (status) {
      case 'Approved':
        return 'check-circle';
      case 'Pending':
        return 'schedule';
      case 'Rejected':
        return 'cancel';
      default:
        return 'help';
    }
  };

  const getStatusColor = status => {
    switch (status) {
      case 'Approved':
        return '#28a745';
      case 'Pending':
        return '#ffc107';
      case 'Rejected':
        return '#dc3545';
      default:
        return '#6c757d';
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <Text>Loading loans...</Text>
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
        <Icon name="account-balance" size={48} color="#007bff" />
        <Text style={styles.title}>My Loans</Text>
        <Text style={styles.subtitle}>Track your loan applications</Text>
      </View>

      {loans.length > 0 ? (
        loans.map((loan, index) => (
          <View key={index} style={styles.loanCard}>
            <View style={styles.loanHeader}>
              <View>
                <Text style={styles.loanAmount}>KSH {loan.amount}</Text>
                <Text style={styles.loanPurpose}>{loan.purpose}</Text>
              </View>
              <View style={styles.statusContainer}>
                <Icon
                  name={getStatusIcon(loan.status)}
                  size={24}
                  color={getStatusColor(loan.status)}
                />
                <Text
                  style={[
                    styles.status,
                    {color: getStatusColor(loan.status)},
                  ]}>
                  {loan.status}
                </Text>
              </View>
            </View>

            <View style={styles.loanDetails}>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Applied:</Text>
                <Text style={styles.detailValue}>
                  {loan.date_applied
                    ? new Date(loan.date_applied).toLocaleDateString()
                    : 'N/A'}
                </Text>
              </View>
              {loan.due_date && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Due Date:</Text>
                  <Text style={styles.detailValue}>
                    {new Date(loan.due_date).toLocaleDateString()}
                  </Text>
                </View>
              )}
            </View>
          </View>
        ))
      ) : (
        <View style={styles.emptyContainer}>
          <Icon name="account-balance" size={64} color="#dee2e6" />
          <Text style={styles.emptyTitle}>No Loans Yet</Text>
          <Text style={styles.emptyText}>
            You haven't applied for any loans yet.
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
  loanCard: {
    backgroundColor: 'white',
    margin: 15,
    borderRadius: 8,
    padding: 20,
    elevation: 2,
  },
  loanHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 15,
  },
  loanAmount: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#007bff',
  },
  loanPurpose: {
    fontSize: 16,
    color: '#333',
    marginTop: 5,
  },
  statusContainer: {
    alignItems: 'center',
  },
  status: {
    fontSize: 12,
    fontWeight: 'bold',
    marginTop: 5,
  },
  loanDetails: {
    borderTopWidth: 1,
    borderTopColor: '#f1f1f1',
    paddingTop: 15,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  detailLabel: {
    fontSize: 14,
    color: '#6c757d',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
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