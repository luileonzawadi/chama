import React, {useState} from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ScrollView,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {chamaAPI} from '../services/api';

export default function ContributeScreen() {
  const [amount, setAmount] = useState('');
  const [phone, setPhone] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);

  const handleContribute = async () => {
    if (!amount || !phone) {
      Alert.alert('Error', 'Please enter amount and phone number');
      return;
    }

    if (parseFloat(amount) <= 0) {
      Alert.alert('Error', 'Amount must be greater than 0');
      return;
    }

    setLoading(true);
    try {
      const response = await chamaAPI.contribute(amount, phone, description);
      if (response.success) {
        Alert.alert('Success', response.message);
        setAmount('');
        setPhone('');
        setDescription('');
      } else {
        Alert.alert('Error', response.message);
      }
    } catch (error) {
      Alert.alert('Error', 'Contribution failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Icon name="account-balance-wallet" size={48} color="#28a745" />
        <Text style={styles.title}>Make Contribution</Text>
        <Text style={styles.subtitle}>
          Contribute to your chama via M-Pesa
        </Text>
      </View>

      <View style={styles.form}>
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Amount (KSH)</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter amount"
            value={amount}
            onChangeText={setAmount}
            keyboardType="numeric"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>M-Pesa Phone Number</Text>
          <TextInput
            style={styles.input}
            placeholder="254712345678"
            value={phone}
            onChangeText={setPhone}
            keyboardType="phone-pad"
          />
          <Text style={styles.helpText}>
            Enter your M-Pesa number (format: 254712345678)
          </Text>
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Description (Optional)</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., Monthly contribution"
            value={description}
            onChangeText={setDescription}
            multiline
          />
        </View>

        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleContribute}
          disabled={loading}>
          <Icon name="phone-android" size={20} color="white" />
          <Text style={styles.buttonText}>
            {loading ? 'Processing...' : 'Pay via M-Pesa'}
          </Text>
        </TouchableOpacity>
      </View>

      <View style={styles.infoCard}>
        <Icon name="info" size={24} color="#007bff" />
        <View style={styles.infoContent}>
          <Text style={styles.infoTitle}>How it works</Text>
          <Text style={styles.infoText}>
            1. Enter your contribution amount{'\n'}
            2. Provide your M-Pesa phone number{'\n'}
            3. Tap "Pay via M-Pesa"{'\n'}
            4. Complete payment on your phone
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
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
  form: {
    backgroundColor: 'white',
    margin: 15,
    borderRadius: 8,
    padding: 20,
    elevation: 2,
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
  input: {
    borderWidth: 1,
    borderColor: '#dee2e6',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#f8f9fa',
  },
  helpText: {
    fontSize: 12,
    color: '#6c757d',
    marginTop: 5,
  },
  button: {
    backgroundColor: '#28a745',
    borderRadius: 8,
    padding: 15,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 10,
  },
  buttonDisabled: {
    backgroundColor: '#6c757d',
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  infoCard: {
    backgroundColor: 'white',
    margin: 15,
    borderRadius: 8,
    padding: 20,
    flexDirection: 'row',
    elevation: 2,
  },
  infoContent: {
    marginLeft: 15,
    flex: 1,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#6c757d',
    lineHeight: 20,
  },
});