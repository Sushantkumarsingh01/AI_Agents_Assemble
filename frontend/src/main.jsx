import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import HomePage from './components/HomePage'
import Login from './components/Login'
import './styles.css'
import 'antd/dist/reset.css'

const container = document.getElementById('root')
if (!container) throw new Error('Root element not found')
const root = createRoot(container)

function Root() {
	// Initialize token from localStorage immediately to prevent flash
	const [token, setToken] = useState(() => {
		const storedToken = localStorage.getItem('token')
		const loginTime = localStorage.getItem('loginTime')
		
		if (storedToken && loginTime) {
			const elapsed = Date.now() - parseInt(loginTime)
			const oneHour = 60 * 60 * 1000
			
			// Return token only if session is still valid
			return elapsed < oneHour ? storedToken : null
		}
		return null
	})
	const authed = useMemo(() => !!token, [token])

	const logout = () => {
		localStorage.removeItem('token')
		localStorage.removeItem('loginTime')
		setToken(null)
	}

	// Set up auto-logout timer if user is logged in
	useEffect(() => {
		if (!token) return
		
		const loginTime = localStorage.getItem('loginTime')
		if (!loginTime) return
		
		const elapsed = Date.now() - parseInt(loginTime)
		const oneHour = 60 * 60 * 1000
		const remainingTime = oneHour - elapsed
		
		if (remainingTime > 0) {
			const timeoutId = setTimeout(() => {
				logout()
				alert('Session expired. Please login again.')
			}, remainingTime)
			
			return () => clearTimeout(timeoutId)
		}
	}, [token])

	function onAuthed(newToken) {
		localStorage.setItem('token', newToken)
		localStorage.setItem('loginTime', Date.now().toString())
		setToken(newToken)
		
		// Set up auto-logout after 1 hour
		setTimeout(() => {
			logout()
			alert('Session expired. Please login again.')
		}, 60 * 60 * 1000) // 1 hour
	}

	return authed ? <HomePage onLogout={logout} /> : <Login onAuthed={onAuthed} />
}

root.render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
) 
