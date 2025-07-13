import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createStackNavigator} from '@react-navigation/stack';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/MaterialIcons';

import LoginScreen from './src/screens/LoginScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import ContributeScreen from './src/screens/ContributeScreen';
import LoansScreen from './src/screens/LoansScreen';
import DiscussionsScreen from './src/screens/DiscussionsScreen';
import ActivitiesScreen from './src/screens/ActivitiesScreen';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({route}) => ({
        tabBarIcon: ({focused, color, size}) => {
          let iconName;
          switch (route.name) {
            case 'Dashboard':
              iconName = 'dashboard';
              break;
            case 'Contribute':
              iconName = 'add-circle';
              break;
            case 'Loans':
              iconName = 'account-balance';
              break;
            case 'Discussions':
              iconName = 'forum';
              break;
            case 'Activities':
              iconName = 'event';
              break;
          }
          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#007bff',
        tabBarInactiveTintColor: 'gray',
      })}>
      <Tab.Screen name="Dashboard" component={DashboardScreen} />
      <Tab.Screen name="Contribute" component={ContributeScreen} />
      <Tab.Screen name="Loans" component={LoansScreen} />
      <Tab.Screen name="Discussions" component={DiscussionsScreen} />
      <Tab.Screen name="Activities" component={ActivitiesScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Login">
        <Stack.Screen 
          name="Login" 
          component={LoginScreen} 
          options={{headerShown: false}}
        />
        <Stack.Screen 
          name="Main" 
          component={MainTabs} 
          options={{headerShown: false}}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}