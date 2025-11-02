import React from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from './layout'
import Home from '../pages/Home'
import Login from '../pages/Auth/Login'
import Accounts from '../pages/Fin/Accounts'
import Categories from '../pages/Fin/Categories'
import Transactions from '../pages/Fin/Transactions'
import { RequireAuth } from '../shared/auth/RequireAuth'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Home /> },
      { path: 'auth/login', element: <Login /> },
      {
        element: <RequireAuth />,
        children: [
          { path: 'fin/accounts', element: <Accounts /> },
          { path: 'fin/categories', element: <Categories /> },
          { path: 'fin/transactions', element: <Transactions /> },
        ],
      },
    ],
  },
])
