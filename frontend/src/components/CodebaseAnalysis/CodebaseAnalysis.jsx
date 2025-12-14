import React, { useState, useEffect } from 'react'
import { Button, Modal, Upload, Input, Select, message, List, Card, Tag, Spin, Popconfirm, Tooltip } from 'antd'
import { UploadOutlined, GithubOutlined, DeleteOutlined, FolderOutlined, FileTextOutlined, CodeOutlined, CopyOutlined, CheckOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import './CodebaseAnalysis.css'

const { TextArea } = Input

export default function CodebaseAnalysis({ token, onClose }) {
	const [projects, setProjects] = useState([])
	const [selectedProject, setSelectedProject] = useState(null)
	const [loading, setLoading] = useState(false)
	const [uploadModalVisible, setUploadModalVisible] = useState(false)
	const [githubModalVisible, setGithubModalVisible] = useState(false)
	
	// Upload form state
	const [uploadFile, setUploadFile] = useState(null)
	const [projectName, setProjectName] = useState('')
	const [projectDescription, setProjectDescription] = useState('')
	const [githubUrl, setGithubUrl] = useState('')
	
	// Analysis state
	const [question, setQuestion] = useState('')
	const [analyzing, setAnalyzing] = useState(false)
	const [analysisResult, setAnalysisResult] = useState(null)
	const [chatHistory, setChatHistory] = useState([]) // Store conversation history
	const [copiedCode, setCopiedCode] = useState(null)
	const [copiedMessage, setCopiedMessage] = useState(null)
	const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

	useEffect(() => {
		loadProjects()
	}, [])
	
	// Copy to clipboard function
	const copyToClipboard = (text, id) => {
		navigator.clipboard.writeText(text).then(() => {
			if (id.startsWith('code-')) {
				setCopiedCode(id)
				setTimeout(() => setCopiedCode(null), 2000)
			} else {
				setCopiedMessage(id)
				setTimeout(() => setCopiedMessage(null), 2000)
			}
			message.success('Copied to clipboard!')
		})
	}

	async function authedFetch(url, options = {}) {
		const headers = {
			...(options.headers || {}),
			...(token ? { Authorization: `Bearer ${token}` } : {})
		}
		return fetch(url, { ...options, headers })
	}

	async function loadProjects() {
		setLoading(true)
		try {
			const res = await authedFetch('/api/codebase/projects')
			if (res.ok) {
				const data = await res.json()
				setProjects(data)
			} else {
				message.error('Failed to load projects')
			}
		} catch (error) {
			message.error('Error loading projects')
		} finally {
			setLoading(false)
		}
	}

	async function handleUploadZip() {
		if (!uploadFile || !projectName.trim()) {
			message.warning('Please provide a project name and select a ZIP file')
			return
		}

		const formData = new FormData()
		formData.append('file', uploadFile)
		formData.append('name', projectName)
		if (projectDescription) {
			formData.append('description', projectDescription)
		}

		setLoading(true)
		try {
			const res = await authedFetch('/api/codebase/upload', {
				method: 'POST',
				body: formData
			})

			if (res.ok) {
				const data = await res.json()
				message.success(data.message)
				setUploadModalVisible(false)
				resetUploadForm()
				await loadProjects()
			} else {
				const error = await res.text()
				message.error(error || 'Upload failed')
			}
		} catch (error) {
			message.error('Error uploading codebase')
		} finally {
			setLoading(false)
		}
	}

	async function handleCloneGithub() {
		if (!githubUrl.trim() || !projectName.trim()) {
			message.warning('Please provide a project name and GitHub URL')
			return
		}

		const formData = new FormData()
		formData.append('repo_url', githubUrl)
		formData.append('name', projectName)
		if (projectDescription) {
			formData.append('description', projectDescription)
		}

		setLoading(true)
		try {
			const res = await authedFetch('/api/codebase/github', {
				method: 'POST',
				body: formData
			})

			if (res.ok) {
				const data = await res.json()
				message.success(data.message)
				setGithubModalVisible(false)
				resetUploadForm()
				await loadProjects()
			} else {
				const error = await res.text()
				message.error(error || 'Clone failed')
			}
		} catch (error) {
			message.error('Error cloning repository')
		} finally {
			setLoading(false)
		}
	}

	async function handleDeleteProject(projectId) {
		try {
			const res = await authedFetch(`/api/codebase/projects/${projectId}`, {
				method: 'DELETE'
			})

			if (res.ok) {
				message.success('Project deleted')
				if (selectedProject?.id === projectId) {
					setSelectedProject(null)
					setAnalysisResult(null)
				}
				await loadProjects()
			} else {
				message.error('Failed to delete project')
			}
		} catch (error) {
			message.error('Error deleting project')
		}
	}

	async function handleAnalyze() {
		if (!selectedProject || !question.trim()) {
			message.warning('Please select a project and enter a question')
			return
		}

		const currentQuestion = question.trim()
		
		// Add user question to chat history
		const newUserMessage = {
			role: 'user',
			content: currentQuestion,
			timestamp: new Date().toISOString()
		}
		setChatHistory(prev => [...prev, newUserMessage])
		setQuestion('') // Clear input immediately

		setAnalyzing(true)
		try {
			const res = await authedFetch('/api/codebase/analyze', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					project_id: selectedProject.id,
					question: currentQuestion,
					chat_history: chatHistory // Send previous chat history
				})
			})

			if (res.ok) {
				const data = await res.json()
				
				// Add assistant response to chat history
				const newAssistantMessage = {
					role: 'assistant',
					content: data.reply,
					relevant_files: data.relevant_files,
					timestamp: new Date().toISOString()
				}
				setChatHistory(prev => [...prev, newAssistantMessage])
				setAnalysisResult(data)
			} else {
				const error = await res.text()
				message.error(error || 'Analysis failed')
			}
		} catch (error) {
			message.error('Error analyzing codebase')
		} finally {
			setAnalyzing(false)
		}
	}
	
	function clearChat() {
		setChatHistory([])
		setAnalysisResult(null)
		setQuestion('')
	}

	function resetUploadForm() {
		setUploadFile(null)
		setProjectName('')
		setProjectDescription('')
		setGithubUrl('')
	}

	const uploadProps = {
		beforeUpload: (file) => {
			if (!file.name.endsWith('.zip')) {
				message.error('Only ZIP files are allowed')
				return false
			}
			setUploadFile(file)
			return false
		},
		onRemove: () => {
			setUploadFile(null)
		},
		fileList: uploadFile ? [uploadFile] : []
	}

	return (
		<div className="codebase-analysis">
			<div className="codebase-header">
				<h2><CodeOutlined /> Codebase Analysis</h2>
				<div className="header-actions">
					<Button 
						type="primary" 
						icon={<UploadOutlined />}
						onClick={() => setUploadModalVisible(true)}
					>
						Upload ZIP
					</Button>
					<Button 
						icon={<GithubOutlined />}
						onClick={() => setGithubModalVisible(true)}
					>
						Clone GitHub
					</Button>
					<Button onClick={onClose}>Close</Button>
				</div>
			</div>

			<div className="codebase-content">
			<div className={`projects-panel ${sidebarCollapsed ? 'collapsed' : ''}`}>
				{!sidebarCollapsed && (
					<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
						<h3 style={{ margin: 0 }}>Your Projects</h3>
						<button 
							className="sidebar-collapse-btn" 
							onClick={() => setSidebarCollapsed(true)}
							title="Collapse sidebar"
						>
							<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
								<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
								<line x1="9" y1="3" x2="9" y2="21"/>
							</svg>
						</button>
					</div>
				)}
				{!sidebarCollapsed && (
					<>
					{loading && projects.length === 0 ? (
						<Spin />
					) : projects.length === 0 ? (
						<p className="empty-state">No projects yet. Upload a codebase to get started!</p>
					) : (
						<List
							dataSource={projects}
							renderItem={(project) => (
								<Card
									key={project.id}
									className={`project-card ${selectedProject?.id === project.id ? 'selected' : ''}`}
									onClick={() => {
										setSelectedProject(project)
										setAnalysisResult(null)
									}}
									hoverable
								>
									<div className="project-info">
										<div className="project-header">
											<FolderOutlined style={{ fontSize: 20, color: '#1890ff' }} />
											<h4>{project.name}</h4>
										</div>
										{project.description && <p className="project-desc">{project.description}</p>}
										<div className="project-meta">
											<Tag color={project.source_type === 'github' ? 'blue' : 'green'}>
												{project.source_type}
											</Tag>
											<span>{project.file_count} files</span>
											<span>{project.total_chunks} chunks</span>
										</div>
									</div>
									<Popconfirm
										title="Delete this project?"
										description="This will permanently delete the project and its vector embeddings."
										onConfirm={(e) => {
											e.stopPropagation()
											handleDeleteProject(project.id)
										}}
										okText="Delete"
										okButtonProps={{ danger: true }}
										cancelText="Cancel"
									>
										<Button
											danger
											size="small"
											icon={<DeleteOutlined />}
											onClick={(e) => e.stopPropagation()}
										/>
									</Popconfirm>
								</Card>
							)}
						/>
					)}
					</>
				)}
			</div>

				<div className="analysis-panel">
				{sidebarCollapsed && (
					<button 
						className="sidebar-expand-btn-floating" 
						onClick={() => setSidebarCollapsed(false)}
						title="Expand sidebar"
					>
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
							<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
							<line x1="9" y1="3" x2="9" y2="21"/>
						</svg>
					</button>
				)}
				{selectedProject ? (
					<>
						<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
							<h3>💬 Chat with: {selectedProject.name}</h3>
							{chatHistory.length > 0 && (
								<Button onClick={clearChat} size="small">Clear Chat</Button>
							)}
						</div>
							
							{/* Chat History */}
							{chatHistory.length > 0 && (
								<div className="chat-history">
									{chatHistory.map((msg, idx) => (
										<div key={idx} className={`chat-message ${msg.role}`}>
											<div className="message-header">
												<strong>{msg.role === 'user' ? '👤 You' : '🤖 AI Assistant'}</strong>
												<span className="message-time">{new Date(msg.timestamp).toLocaleTimeString()}</span>
											</div>
											<div className="message-content">
												{msg.role === 'user' ? (
													<p>{msg.content}</p>
												) : (
													<>
														<ReactMarkdown
															remarkPlugins={[remarkGfm]}
															components={{
																code({ node, inline, className, children, ...props }) {
																	const match = /language-(\w+)/.exec(className || '')
																	const codeString = String(children).replace(/\n$/, '')
																	const codeId = `code-${idx}-${Math.random()}`
																	
																	return !inline && match ? (
																		<div className="code-block-wrapper">
																			<div className="code-block-header">
																				<span className="code-language">{match[1]}</span>
																				<Tooltip title={copiedCode === codeId ? "Copied!" : "Copy code"}>
																					<Button
																						size="small"
																						icon={copiedCode === codeId ? <CheckOutlined /> : <CopyOutlined />}
																						onClick={() => copyToClipboard(codeString, codeId)}
																						className="copy-code-btn"
																					/>
																				</Tooltip>
																			</div>
																			<SyntaxHighlighter
																				style={vscDarkPlus}
																				language={match[1]}
																				PreTag="div"
																				{...props}
																			>
																				{codeString}
																			</SyntaxHighlighter>
																		</div>
																	) : (
																		<code className={className} {...props}>
																			{children}
																		</code>
																	)
																},
																h1: ({ children }) => <h1 className="md-h1">{children}</h1>,
																h2: ({ children }) => <h2 className="md-h2">{children}</h2>,
																h3: ({ children }) => <h3 className="md-h3">{children}</h3>,
																ul: ({ children }) => <ul className="md-list">{children}</ul>,
																ol: ({ children }) => <ol className="md-list">{children}</ol>,
																li: ({ children }) => <li className="md-list-item">{children}</li>,
																blockquote: ({ children }) => <blockquote className="md-blockquote">{children}</blockquote>,
																a: ({ href, children }) => <a href={href} className="md-link" target="_blank" rel="noopener noreferrer">{children}</a>,
																table: ({ children }) => <table className="md-table">{children}</table>,
																strong: ({ children }) => <strong className="md-strong">{children}</strong>,
															}}
														>
															{msg.content}
														</ReactMarkdown>
														{msg.relevant_files && msg.relevant_files.length > 0 && (
															<div className="relevant-files-inline">
																<FileTextOutlined /> <strong>Files:</strong> {msg.relevant_files.join(', ')}
															</div>
														)}
														<div className="message-actions">
															<Tooltip title={copiedMessage === `msg-${idx}` ? "Copied!" : "Copy response"}>
																<Button
																	size="small"
																	icon={copiedMessage === `msg-${idx}` ? <CheckOutlined /> : <CopyOutlined />}
																	onClick={() => copyToClipboard(msg.content, `msg-${idx}`)}
																	className="copy-message-btn"
																>
																	Copy Response
																</Button>
															</Tooltip>
														</div>
													</>
												)}
											</div>
										</div>
									))}
								</div>
							)}
							
							<div className="analysis-input">
								<TextArea
									value={question}
									onChange={(e) => setQuestion(e.target.value)}
									onPressEnter={(e) => {
										if (e.ctrlKey || e.metaKey) {
											handleAnalyze()
										}
									}}
									placeholder="Ask anything about this codebase... (Ctrl+Enter to send)"
									rows={3}
									disabled={analyzing}
								/>
								<Button
									type={question.trim() ? "primary" : "default"}
									size="large"
									onClick={handleAnalyze}
									loading={analyzing}
									disabled={!question.trim()}
									style={{
										background: question.trim() ? undefined : '#1a1f2e',
										borderColor: question.trim() ? undefined : '#2d3748',
										color: question.trim() ? undefined : '#64748b'
									}}
								>
									{analyzing ? 'Analyzing...' : chatHistory.length > 0 ? 'Continue Chat' : 'Start Analysis'}
								</Button>
							</div>
						</>
					) : (
						<div className="empty-analysis">
							<CodeOutlined style={{ fontSize: 64, color: '#ccc' }} />
							<p>Select a project to start analyzing</p>
						</div>
					)}
				</div>
			</div>

			{/* Upload ZIP Modal */}
			<Modal
				title="Upload Codebase (ZIP)"
				open={uploadModalVisible}
				onOk={handleUploadZip}
				onCancel={() => {
					setUploadModalVisible(false)
					resetUploadForm()
				}}
				confirmLoading={loading}
			>
				<div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
					<Input
						placeholder="Project Name *"
						value={projectName}
						onChange={(e) => setProjectName(e.target.value)}
					/>
					<TextArea
						placeholder="Description (optional)"
						value={projectDescription}
						onChange={(e) => setProjectDescription(e.target.value)}
						rows={3}
					/>
					<Upload {...uploadProps}>
						<Button icon={<UploadOutlined />}>Select ZIP File</Button>
					</Upload>
				</div>
			</Modal>

			{/* GitHub Clone Modal */}
			<Modal
				title="Clone GitHub Repository"
				open={githubModalVisible}
				onOk={handleCloneGithub}
				onCancel={() => {
					setGithubModalVisible(false)
					resetUploadForm()
				}}
				confirmLoading={loading}
			>
				<div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
					<Input
						placeholder="Project Name *"
						value={projectName}
						onChange={(e) => setProjectName(e.target.value)}
					/>
					<TextArea
						placeholder="Description (optional)"
						value={projectDescription}
						onChange={(e) => setProjectDescription(e.target.value)}
						rows={3}
					/>
					<Input
						placeholder="GitHub Repository URL *"
						value={githubUrl}
						onChange={(e) => setGithubUrl(e.target.value)}
						prefix={<GithubOutlined />}
					/>
				</div>
			</Modal>
		</div>
	)
}
