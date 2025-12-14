import React, { useState } from 'react'
import { Upload, message } from 'antd'
import { PaperClipOutlined, CloseCircleOutlined, FileImageOutlined, FilePdfOutlined } from '@ant-design/icons'

const MAX_FILE_SIZE = 2 * 1024 * 1024 // 2MB
const ALLOWED_TYPES = [
	'image/jpeg',
	'image/jpg',
	'image/png',
	'image/gif',
	'image/webp',
	'application/pdf'
]

export default function FileUpload({ 
	onFilesChange, 
	disabled, 
	showPreviewList = false,
	fileList: externalFileList,
	attachments: externalAttachments,
	onFileListChange,
	onAttachmentsChange
}) {
	const [internalFileList, setInternalFileList] = useState([])
	const [internalAttachments, setInternalAttachments] = useState([])
	
	// Use external state if provided, otherwise use internal state
	const fileList = externalFileList !== undefined ? externalFileList : internalFileList
	const attachments = externalAttachments !== undefined ? externalAttachments : internalAttachments
	
	const setFileList = (files) => {
		if (onFileListChange) {
			onFileListChange(files)
		} else {
			setInternalFileList(files)
		}
	}
	
	const setAttachments = (atts) => {
		if (onAttachmentsChange) {
			onAttachmentsChange(atts)
		} else {
			setInternalAttachments(atts)
		}
	}

	const handleFileChange = async (file) => {
		// Validate file type
		if (!ALLOWED_TYPES.includes(file.type)) {
			message.error('Only images (JPG, PNG, GIF, WEBP) and PDF files are allowed')
			return false
		}

		// Validate file size
		if (file.size > MAX_FILE_SIZE) {
			message.error('File size must be less than 2MB')
			return false
		}

		try {
			// Convert to base64
			const base64 = await fileToBase64(file)
			
			const newAttachment = {
				filename: file.name,
				mime_type: file.type,
				data: base64
			}

			const newAttachments = [...attachments, newAttachment]
			setAttachments(newAttachments)
			onFilesChange(newAttachments)

			return true
		} catch (error) {
			message.error('Failed to process file')
			return false
		}
	}

	const fileToBase64 = (file) => {
		return new Promise((resolve, reject) => {
			const reader = new FileReader()
			reader.readAsDataURL(file)
			reader.onload = () => {
				const result = reader.result
				// Remove data URL prefix (e.g., "data:image/png;base64,")
				const base64 = result.split(',')[1]
				resolve(base64)
			}
			reader.onerror = reject
		})
	}

	const handleRemove = (file) => {
		const newFileList = fileList.filter(f => f.uid !== file.uid)
		const newAttachments = attachments.filter((_, index) => {
			const fileIndex = fileList.findIndex(f => f.uid === file.uid)
			return index !== fileIndex
		})
		
		setFileList(newFileList)
		setAttachments(newAttachments)
		onFilesChange(newAttachments)
	}

	const beforeUpload = (file) => {
		handleFileChange(file).then(success => {
			if (success) {
				setFileList([...fileList, {
					uid: `${Date.now()}-${file.name}`,
					name: file.name,
					status: 'done',
					size: file.size,
					type: file.type
				}])
			}
		})
		return false // Prevent auto upload
	}

	const getFileIcon = (type) => {
		if (type.startsWith('image/')) {
			return <FileImageOutlined style={{ fontSize: 16, color: '#10b981' }} />
		}
		if (type === 'application/pdf') {
			return <FilePdfOutlined style={{ fontSize: 16, color: '#ef4444' }} />
		}
		return <PaperClipOutlined style={{ fontSize: 16 }} />
	}

	if (showPreviewList) {
		// Render only the preview list (for display above composer)
		return (
			<>
				{fileList.length > 0 && (
					<div className="file-attachments-preview">
						<div className="file-attachments-header">
							<span>Attached Files ({fileList.length})</span>
						</div>
						<div className="file-attachments-list">
							{fileList.map(file => (
								<div key={file.uid} className="file-attachment-chip">
									{getFileIcon(file.type || '')}
									<span className="file-attachment-name">{file.name}</span>
									<span className="file-attachment-size">
										{((file.size || 0) / 1024).toFixed(1)}KB
									</span>
									<button
										type="button"
										className="file-attachment-remove"
										onClick={() => handleRemove(file)}
										title="Remove file"
									>
										<CloseCircleOutlined />
									</button>
								</div>
							))}
						</div>
					</div>
				)}
			</>
		)
	}

	// Render only the upload button (for composer)
	return (
		<Upload
			beforeUpload={beforeUpload}
			onRemove={handleRemove}
			fileList={fileList}
			showUploadList={false}
			disabled={disabled}
			multiple
			accept=".jpg,.jpeg,.png,.gif,.webp,.pdf"
		>
			<button 
				type="button" 
				className="file-upload-btn" 
				disabled={disabled}
				title="Attach files (Images or PDF, max 2MB)"
			>
				<PaperClipOutlined />
				{fileList.length > 0 && (
					<span className="file-upload-badge">{fileList.length}</span>
				)}
			</button>
		</Upload>
	)
}
