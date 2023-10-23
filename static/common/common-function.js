function hideMyToast() {
    const activeToast = document.querySelectorAll('.toastify.on')
    activeToast.forEach(function(item) {
        item.className = item.className.replace(" on", "")
    })
}