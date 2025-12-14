import React, { useState } from 'react'
import { Button, Form, Input, Typography, message } from 'antd'
import './Login.css'

export default function Login({ onAuthed }) {
	const [loading, setLoading] = useState(false)
	const [mode, setMode] = useState('login')

	async function request(path, body) {
		const res = await fetch(`/api${path}`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(body),
		})
		if (!res.ok) {
			const detail = await res.text()
			throw new Error(detail || 'Request failed')
		}
		return res.json()
	}

	async function handleLogin(values) {
		setLoading(true)
		try {
			const data = await request('/auth/login', values)
			onAuthed(data.access_token)
			message.success('Welcome back!')
		} catch (e) {
			message.error(e?.message || 'Login failed')
		} finally {
			setLoading(false)
		}
	}

	async function handleSignup(values) {
		setLoading(true)
		try {
			const data = await request('/auth/signup', values)
			onAuthed(data.access_token)
			message.success('Account created!')
		} catch (e) {
			message.error(e?.message || 'Signup failed')
		} finally {
			setLoading(false)
		}
	}

	function forgotPassword() {
		message.info('Password reset is not configured yet.')
	}

	return (
		<div className="auth-grid">
			<div className="auth-left hero">
				<div className="auth-card">
					<Typography.Title className="auth-title" level={1}>{mode === 'login' ? 'LOGIN' : 'SIGN UP'}</Typography.Title>
					{mode === 'login' ? (
						<>
							<Form layout="vertical" onFinish={handleLogin} disabled={loading}>
								<Form.Item label="Email" name="email" rules={[{ required: true, type: 'email' }]}>
									<Input placeholder="Email" size="large" />
								</Form.Item>
								<Form.Item label="Password" name="password" rules={[{ required: true, min: 6 }]}>
									<Input.Password placeholder="Password" size="large" />
								</Form.Item>
								<div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
									<button type="button" className="auth-link" onClick={forgotPassword}>Forgot password?</button>
								</div>
								<Button type="primary" htmlType="submit" size="large" block loading={loading}>LOG IN</Button>
							</Form>
							<div className="auth-muted" style={{ marginTop: 16 }}>Don't have an account? <button type="button" className="auth-link" onClick={() => setMode('signup')}>Sign up</button></div>
						</>
					) : (
						<>
							<Form layout="vertical" onFinish={handleSignup} disabled={loading}>
								<Form.Item label="Email" name="email" rules={[{ required: true, type: 'email' }]}>
									<Input placeholder="Email" size="large" />
								</Form.Item>
								<Form.Item label="Password" name="password" rules={[{ required: true, min: 6 }]}>
									<Input.Password placeholder="Create a strong password" size="large" />
								</Form.Item>
								<Button type="primary" htmlType="submit" size="large" block loading={loading}>Create account</Button>
							</Form>
							<div className="auth-muted" style={{ marginTop: 16 }}>Already have an account? <button type="button" className="auth-link" onClick={() => setMode('login')}>Log in</button></div>
						</>
					)}
				</div>
			</div>
			<div className="auth-right">
				<img src="/loginpageimg.png" alt="AI" className="auth-image" />
			</div>
		</div>
	)
}
