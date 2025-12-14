import React, { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { CopyOutlined, CheckOutlined } from '@ant-design/icons'

export default function CodeBlock({ language, children }) {
	const [copied, setCopied] = useState(false)

	const handleCopy = async () => {
		try {
			await navigator.clipboard.writeText(children)
			setCopied(true)
			setTimeout(() => setCopied(false), 2000)
		} catch (err) {
			console.error('Failed to copy:', err)
		}
	}

	return (
		<div className="code-block-wrapper">
			<div className="code-block-header">
				<span className="code-block-language">{language}</span>
				<button 
					className="code-block-copy-btn" 
					onClick={handleCopy}
					title={copied ? 'Copied!' : 'Copy code'}
				>
					{copied ? <CheckOutlined /> : <CopyOutlined />}
					<span>{copied ? 'Copied!' : 'Copy'}</span>
				</button>
			</div>
			<SyntaxHighlighter
				style={vscDarkPlus}
				language={language}
				PreTag="div"
				customStyle={{
					margin: 0,
					borderRadius: '0 0 8px 8px',
					padding: '16px',
				}}
			>
				{children}
			</SyntaxHighlighter>
		</div>
	)
}
