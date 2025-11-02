import React from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from './layout'
import Home from '../pages/Home'
import Login from '../pages/Auth/Login'
import Accounts from '../pages/Fin/Accounts'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Home /> },
      { path: 'auth/login', element: <Login /> },
      { path: 'fin/accounts', element: <Accounts /> },
    ],
  },
])
