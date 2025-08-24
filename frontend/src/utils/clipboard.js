/**
 * Robust clipboard utility with async Clipboard API and fallbacks
 */

export const copyToClipboard = async (text) => {
  try {
    // Modern async Clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return { success: true, method: 'clipboard-api' };
    }
    
    // Fallback for older browsers or insecure contexts
    return await fallbackCopyTextToClipboard(text);
  } catch (error) {
    console.warn('Clipboard API failed, trying fallback:', error);
    return await fallbackCopyTextToClipboard(text);
  }
};

const fallbackCopyTextToClipboard = (text) => {
  return new Promise((resolve, reject) => {
    try {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      
      // Make the textarea out of viewport
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      textArea.style.opacity = '0';
      textArea.style.pointerEvents = 'none';
      
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      
      // For mobile devices
      textArea.setSelectionRange(0, 99999);
      
      const successful = document.execCommand('copy');
      document.body.removeChild(textArea);
      
      if (successful) {
        resolve({ success: true, method: 'execCommand' });
      } else {
        reject(new Error('execCommand copy failed'));
      }
    } catch (error) {
      reject(error);
    }
  });
};

// Enhanced copy with user feedback
export const copyWithFeedback = async (text, options = {}) => {
  const {
    successMessage = 'Copied to clipboard!',
    errorMessage = 'Failed to copy. Please copy manually.',
    onSuccess,
    onError
  } = options;
  
  try {
    const result = await copyToClipboard(text);
    
    if (result.success) {
      if (onSuccess) {
        onSuccess(successMessage, result);
      }
      return { success: true, message: successMessage };
    } else {
      throw new Error('Copy operation failed');
    }
  } catch (error) {
    console.error('Copy failed:', error);
    
    if (onError) {
      onError(errorMessage, error);
    }
    
    return { success: false, message: errorMessage, error };
  }
};