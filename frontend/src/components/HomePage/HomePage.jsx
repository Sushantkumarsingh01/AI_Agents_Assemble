import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Button, Popconfirm, Dropdown, Avatar, message } from 'antd'
import { DeleteOutlined, UserOutlined, LogoutOutlined, CopyOutlined, ReloadOutlined, CheckOutlined, AudioOutlined, LeftOutlined, RightOutlined, CodeOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CodeBlock from './CodeBlock'
import FileUpload from './FileUpload'
import GeneratedImage from './GeneratedImage'
import CodebaseAnalysis from '../CodebaseAnalysis'
import './HomePage.css'

const initialSystem = {
	role: 'system',
	content:
		'You are a humble, polite, and very helpful AI assistant. Answer with kindness and clarity.',
}

function decodeEmailFromToken(token) {
	if (!token) return null
	try {
		const [, payload] = token.split('.')
		const json = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
		return json?.sub ?? null
	} catch {
		return null
	}
}

const loadingPhrases = [
	'Analyzing your question…',
	'Generating the perfect response…',
	'Adding a touch of magic…',
	'Almost there…',
]

export default function HomePage({ onLogout }) {
	const [messages, setMessages] = useState([initialSystem])
	const [input, setInput] = useState('')
	const [loading, setLoading] = useState(false)
	const [sidebarOpen, setSidebarOpen] = useState(true)
	const [conversations, setConversations] = useState([])
	const [activeConversationId, setActiveConversationId] = useState(null)
	const [token] = useState(() => localStorage.getItem('token'))
	const userEmail = useMemo(() => decodeEmailFromToken(token), [token])
	const scrollRef = useRef(null)
	const [phraseIndex, setPhraseIndex] = useState(0)
	const [currentAttachments, setCurrentAttachments] = useState([])
	const [currentFileList, setCurrentFileList] = useState([])
	const [copiedIndex, setCopiedIndex] = useState(null)
	const [isListening, setIsListening] = useState(false)
	const recognitionRef = useRef(null)
	const [showCodebaseAnalysis, setShowCodebaseAnalysis] = useState(false)

	useEffect(() => {
		if (!token) return
		loadConversations()
	}, [token])

	useEffect(() => {
		// Initialize Speech Recognition
		if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
			const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
			recognitionRef.current = new SpeechRecognition()
			recognitionRef.current.continuous = false
			recognitionRef.current.interimResults = true
			recognitionRef.current.lang = 'en-US'

			recognitionRef.current.onresult = (event) => {
				const transcript = Array.from(event.results)
					.map(result => result[0])
					.map(result => result.transcript)
					.join('')
				
				setInput(transcript)
			}

			recognitionRef.current.onerror = (event) => {
				console.error('Speech recognition error:', event.error)
				setIsListening(false)
				if (event.error === 'not-allowed') {
					message.error('Microphone access denied. Please allow microphone access.')
				} else if (event.error !== 'no-speech') {
					message.error('Voice recognition error. Please try again.')
				}
			}

			recognitionRef.current.onend = () => {
				setIsListening(false)
			}
		}

		return () => {
			if (recognitionRef.current) {
				recognitionRef.current.stop()
			}
		}
	}, [])

	useEffect(() => {
		scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
	}, [messages, loading])

	useEffect(() => {
		if (!loading) return
		const id = setInterval(() => {
			setPhraseIndex((i) => (i + 1) % loadingPhrases.length)
		}, 1200)
		return () => clearInterval(id)
	}, [loading])

	const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading])

	async function authedFetch(input, init) {
		const headers = { ...(init?.headers || {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) }
		const response = await fetch(input, { ...init, headers })
		
		// Auto-logout on 401 Unauthorized
		if (response.status === 401) {
			localStorage.removeItem('token')
			if (onLogout) {
				onLogout()
			} else {
				window.location.reload()
			}
		}
		
		return response
	}

	async function loadConversations() {
		try {
			const res = await authedFetch('/api/conversations')
			if (!res.ok) throw new Error('Failed to load conversations')
			const data = await res.json()
			setConversations(data)
		} catch (e) {
			// ignore for now
		}
	}

	async function newChat() {
		try {
			const res = await authedFetch('/api/conversations', { method: 'POST' })
			if (!res.ok) throw new Error('Failed to create conversation')
			const conv = await res.json()
			setActiveConversationId(conv.id)
			setMessages([initialSystem])
			// Clear attachments for new chat
			setCurrentAttachments([])
			setCurrentFileList([])
			await loadConversations()
		} catch (e) {
			// ignore
		}
	}

	async function openConversation(id) {
		try {
			const res = await authedFetch(`/api/conversations/${id}/messages`)
			if (!res.ok) throw new Error('Failed to load messages')
			const data = await res.json()
			
			const history = [
				initialSystem, 
				...data.map(m => ({ 
					role: m.role, 
					content: m.content,
					attachments: m.attachments,
					generated_image: m.generated_image
				}))
			]
			
			setActiveConversationId(id)
			setMessages(history)
			
			// Load attachments from the last user message
			const lastUserMessage = [...data].reverse().find(m => m.role === 'user')
			if (lastUserMessage && lastUserMessage.attachments) {
				setCurrentAttachments(lastUserMessage.attachments)
				// Reconstruct file list for UI
				const fileList = lastUserMessage.attachments.map((att, idx) => ({
					uid: `${Date.now()}-${idx}`,
					name: att.filename,
					status: 'done',
					size: Math.round(att.data.length * 0.75), // Approximate size from base64
					type: att.mime_type
				}))
				setCurrentFileList(fileList)
			} else {
				// Clear attachments if no files in conversation
				setCurrentAttachments([])
				setCurrentFileList([])
			}
			
			// Show a subtle notification that conversation history is loaded
			if (data.length > 0) {
				console.log(`Loaded ${data.length} messages from conversation history`)
			}
		} catch (e) {
			// ignore
		}
	}

	async function deleteConversation(id) {
		try {
			const res = await authedFetch(`/api/conversations/${id}`, { method: 'DELETE' })
			if (!res.ok) throw new Error('Failed to delete conversation')
			setConversations(prev => prev.filter(c => c.id != id))
			if (activeConversationId === id) {
				setActiveConversationId(null)
				setMessages([initialSystem])
			}
		} catch (e) {
			// ignore for now
		}
	}

	async function sendMessage(e) {
		e?.preventDefault()
		if (!canSend) return
		const userMessage = { 
			role: 'user', 
			content: input.trim(),
			attachments: currentAttachments.length > 0 ? currentAttachments : undefined
		}
		setMessages((prev) => [...prev, userMessage])
		setInput('')
		// DON'T clear attachments - keep them for next message
		// setCurrentAttachments([])
		// setCurrentFileList([])
		setLoading(true)
		try {
			const res = await authedFetch('/api/chat', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ messages: [...messages, userMessage], conversation_id: activeConversationId }),
			})
			if (!res.ok) {
				const detail = await res.text()
				throw new Error(detail || 'Request failed')
			}
			const data = await res.json()
			const usedId = data.conversation_id ?? activeConversationId
			if (usedId && usedId !== activeConversationId) {
				setActiveConversationId(usedId)
				await loadConversations()
			}
			const assistantMessage = { 
				role: 'assistant', 
				content: data.reply,
				generated_image: data.generated_image
			}
			setMessages((prev) => [...prev, assistantMessage])
		} catch (err) {
			setMessages((prev) => [
				...prev,
				{ role: 'assistant', content: `Sorry, something went wrong: ${err?.message || err}` },
			])
		} finally {
			setLoading(false)
		}
	}

	function handleKeyDown(e) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault()
			sendMessage()
		}
	}

	function toggleVoiceInput() {
		if (!recognitionRef.current) {
			message.warning('Voice recognition is not supported in your browser. Please use Chrome, Edge, or Safari.')
			return
		}

		if (isListening) {
			recognitionRef.current.stop()
			setIsListening(false)
		} else {
			try {
				recognitionRef.current.start()
				setIsListening(true)
				message.info('Listening... Speak now')
			} catch (error) {
				console.error('Error starting recognition:', error)
				message.error('Failed to start voice recognition')
			}
		}
	}

	async function handleCopyResponse(content, idx) {
		try {
			await navigator.clipboard.writeText(content)
			setCopiedIndex(idx)
			message.success('Response copied to clipboard!')
			setTimeout(() => setCopiedIndex(null), 2000)
		} catch (err) {
			message.error('Failed to copy response')
		}
	}

	async function handleRegenerateResponse(idx) {
		if (loading) return
		
		// Find the user message that prompted this assistant response
		const assistantMessages = messages.filter(m => m.role === 'assistant')
		const assistantIdx = assistantMessages.findIndex((_, i) => {
			const filteredIdx = messages.filter(m => m.role !== 'system').findIndex(m => m.role === 'assistant' && messages.indexOf(m) === messages.filter(msg => msg === assistantMessages[i])[0])
			return filteredIdx === idx
		})
		
		// Get all messages up to (but not including) this assistant message
		const messagesUpToHere = messages.slice(0, messages.indexOf(assistantMessages[assistantIdx]))
		
		// Remove this and all subsequent messages
		setMessages(messagesUpToHere)
		setLoading(true)
		
		try {
			const res = await authedFetch('/api/chat', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ messages: messagesUpToHere, conversation_id: activeConversationId }),
			})
			if (!res.ok) {
				const detail = await res.text()
				throw new Error(detail || 'Request failed')
			}
			const data = await res.json()
			const assistantMessage = { 
				role: 'assistant', 
				content: data.reply,
				generated_image: data.generated_image
			}
			setMessages((prev) => [...prev, assistantMessage])
		} catch (err) {
			setMessages((prev) => [
				...prev,
				{ role: 'assistant', content: `Sorry, something went wrong: ${err?.message || err}` },
			])
		} finally {
			setLoading(false)
		}
	}

	function logout() {
		if (onLogout) {
			onLogout()
		} else {
			localStorage.removeItem('token')
			window.location.reload()
		}
	}

	const profileMenu = {
		items: [
			{ key: 'email', label: userEmail || 'Account', disabled: true },
			{ type: 'divider' },
			{ key: 'logout', label: (
				<div style={{ display: 'flex', alignItems: 'center', gap: 8 }} onClick={logout}>
					<LogoutOutlined /> Logout
				</div>
			)},
		],
	}

	if (!token) {
		return (
			<div className="app" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
				<div style={{ color: '#cbd5e1' }}>
					You are not logged in. Implement the Login page to continue.
				</div>
			</div>
		)
	}

	if (showCodebaseAnalysis) {
		return <CodebaseAnalysis token={token} onClose={() => setShowCodebaseAnalysis(false)} />
	}

	return (
		<div className="app" style={{ display: 'grid', gridTemplateColumns: sidebarOpen ? '260px 1fr' : '0 1fr' }}>
			<aside className="sidebar" style={{ borderRight: '1px solid #202432', padding: sidebarOpen ? 12 : 0, overflow: 'hidden' }}>
				{sidebarOpen && (
					<div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
						<div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
							<Button type="primary" onClick={newChat} style={{ flex: 1 }}>+ New Chat</Button>
							<button className="sidebar-collapse-btn" onClick={() => setSidebarOpen(false)} title="Close sidebar">
								<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
									<rect x="3" y="3" width="18" height="18" rx="2" />
									<line x1="9" y1="3" x2="9" y2="21" />
									<path d="M14 15l-3-3 3-3" />
								</svg>
							</button>
						</div>
						<div style={{ overflow: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
							{conversations.map((c) => (
								<div key={c.id} className="conv-row">
									<button className="conv-open" onClick={() => openConversation(c.id)} title={c.title}>
										{c.title}
									</button>
									<Popconfirm
										title="Delete chat?"
										description="This will permanently delete this conversation."
										onConfirm={() => deleteConversation(c.id)}
										okText="Delete"
										okButtonProps={{ danger: true }}
										cancelText="Cancel"
									>
										<Button danger icon={<DeleteOutlined />} aria-label="Delete conversation" />
									</Popconfirm>
								</div>
							))}
						</div>
						<Button 
							icon={<CodeOutlined />} 
							onClick={() => setShowCodebaseAnalysis(true)}
							className="codebase-analyze-btn"
							style={{ marginTop: 12, width: '100%' }}
						>
							<span className="sparkle-dot sparkle-1"></span>
							<span className="sparkle-dot sparkle-2"></span>
							<span className="sparkle-dot sparkle-3"></span>
							<span className="sparkle-dot sparkle-4"></span>
							<span className="sparkle-dot sparkle-5"></span>
							<span className="sparkle-dot sparkle-6"></span>
							<span className="sparkle-dot sparkle-7"></span>
							<span className="sparkle-dot sparkle-8"></span>
							<span style={{ position: 'relative', zIndex: 1 }}>✨ Analyze Codebase</span>
						</Button>
					</div>
				)}
			</aside>
			<div className="main">
				<header className="app__header" style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'space-between' }}>
					<div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
						{!sidebarOpen && (
							<button className="sidebar-expand-btn" onClick={() => setSidebarOpen(true)} title="Open sidebar">
								<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
									<rect x="3" y="3" width="18" height="18" rx="2" />
									<line x1="9" y1="3" x2="9" y2="21" />
									<path d="M14 9l3 3-3 3" />
								</svg>
							</button>
						)}
						<span>AI Chatbot</span>
					</div>
					<div>
						<Dropdown menu={profileMenu} placement="bottomRight" trigger={["click"]}>
							<div style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
								<Avatar size={28} icon={<UserOutlined />} />
								<span style={{ color: '#cbd5e1', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis' }}>{userEmail || 'Me'}</span>
							</div>
						</Dropdown>
					</div>
				</header>
				<main className="app__main">
					<div className="chat" ref={scrollRef}>
						{messages.filter((m) => m.role !== 'system').map((m, idx) => (
						<div key={idx} className={`bubble bubble--${m.role}`}>
							{m.role === 'assistant' ? (
								<>
									<div className="message-content">
										<ReactMarkdown
											remarkPlugins={[remarkGfm]}
											components={{
												code({ node, inline, className, children, ...props }) {
													const match = /language-(\w+)/.exec(className || '')
													const codeString = String(children).replace(/\n$/, '')
													return !inline && match ? (
														<CodeBlock language={match[1]}>{codeString}</CodeBlock>
													) : (
														<code className={className} {...props}>
															{children}
														</code>
													)
												}
											}}
										>
											{m.content}
										</ReactMarkdown>
										{m.generated_image && (
											<GeneratedImage 
												prompt={m.generated_image.prompt}
												imageUrl={m.generated_image.image_url}
												imageData={m.generated_image.image_data}
											/>
										)}
									</div>
									<div className="message-actions">
										<button 
											className="message-action-btn"
											onClick={() => handleCopyResponse(m.content, idx)}
											title="Copy response"
										>
											{copiedIndex === idx ? <CheckOutlined /> : <CopyOutlined />}
										</button>
										<button 
											className="message-action-btn"
											onClick={() => handleRegenerateResponse(idx)}
											title="Regenerate response"
											disabled={loading}
										>
											<ReloadOutlined />
										</button>
									</div>
								</>
							) : (
								m.content
							)}
						</div>
					))}
						{loading && (
							<div className="bubble bubble--assistant bubble--typing">
								<div className="siri">
									<span /><span /><span /><span /><span />
								</div>
								<div className="loader-text">{loadingPhrases[phraseIndex]}</div>
							</div>
						)}
					</div>
					{isListening && (
						<div className="voice-overlay" onClick={toggleVoiceInput}>
							<div className="voice-animation-container" onClick={(e) => e.stopPropagation()}>
								<div className="voice-ripple"></div>
								<div className="voice-ripple"></div>
								<div className="voice-ripple"></div>
								<div className="voice-orb" onClick={toggleVoiceInput}>
									<AudioOutlined />
								</div>
								<div className="voice-bars">
									<span /><span /><span /><span /><span />
									<span /><span /><span /><span /><span />
								</div>
								<div className="voice-text">Listening...</div>
								<div className="voice-hint">Speak now or click mic to stop</div>
							</div>
						</div>
					)}
				</main>
				<FileUpload 
					onFilesChange={setCurrentAttachments} 
					disabled={loading}
					showPreviewList={true}
					fileList={currentFileList}
					attachments={currentAttachments}
					onFileListChange={setCurrentFileList}
					onAttachmentsChange={setCurrentAttachments}
				/>
				<form className="composer" onSubmit={sendMessage}>
					<FileUpload 
						onFilesChange={setCurrentAttachments} 
						disabled={loading}
						fileList={currentFileList}
						attachments={currentAttachments}
						onFileListChange={setCurrentFileList}
						onAttachmentsChange={setCurrentAttachments}
					/>
					<div className="textarea-container">
						<textarea
							value={input}
							onChange={(e) => setInput(e.target.value)}
							onKeyDown={handleKeyDown}
							placeholder="Message AI…"
							rows={1}
						/>
						<button 
							type="button"
							className={`voice-input-btn ${isListening ? 'listening' : ''}`}
							onClick={toggleVoiceInput}
							title={isListening ? 'Stop listening' : 'Voice input'}
							disabled={loading}
						>
							<AudioOutlined />
						</button>
					</div>
					<button type="submit" disabled={!canSend}>Send</button>
				</form>
			</div>
		</div>
	)
}
