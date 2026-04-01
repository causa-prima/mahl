import { Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle } from '@mui/material';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  content: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({ open, title, content, confirmLabel = 'Löschen', onConfirm, onCancel }: ConfirmDialogProps) {
  return (
    <Dialog open={open} onClose={onCancel} maxWidth="xs" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <DialogContentText>{content}</DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel} autoFocus>Abbrechen</Button>
        <Button onClick={onConfirm} color="error" variant="contained">{confirmLabel}</Button>
      </DialogActions>
    </Dialog>
  );
}
