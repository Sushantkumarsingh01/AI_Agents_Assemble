import React from 'react'
import { DownloadOutlined } from '@ant-design/icons'
import { message } from 'antd'

export default function GeneratedImage({ prompt, imageData, imageUrl }) {
	const handleDownload = () => {
		try {
			// Create a download link
			const link = document.createElement('a')
			link.href = `data:image/png;base64,${imageData}`
			link.download = `generated-${Date.now()}.png`
			document.body.appendChild(link)
			link.click()
			document.body.removeChild(link)
			message.success('Image downloaded successfully!')
		} catch (error) {
			message.error('Failed to download image')
		}
	}

	return (
		<div className="generated-image-container">
			<div className="generated-image-header">
				<span className="generated-image-prompt">🎨 Generated: {prompt}</span>
			</div>
			<div className="generated-image-wrapper">
				<img 
					src={`data:image/png;base64,${imageData}`}
					alt={prompt}
					className="generated-image"
				/>
			</div>
			<div className="generated-image-actions">
				<button 
					className="generated-image-download-btn"
					onClick={handleDownload}
					title="Download image"
				>
					<DownloadOutlined />
					<span>Download Image</span>
				</button>
			</div>
		</div>
	)
}
