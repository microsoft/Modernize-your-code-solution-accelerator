import React from "react";
import { Dialog, DialogSurface, DialogBody, DialogTitle, DialogContent, DialogActions } from "@fluentui/react-components";
import { Button } from "@fluentui/react-components";
import { Dismiss24Regular } from "@fluentui/react-icons";
import "./confirmationDialogue.scss";

const ConfirmationDialog = ({ open, setOpen, title, message, confirmText, cancelText, onConfirm, onCancel }) => {
    return (
        <Dialog open={open} onOpenChange={(event, data) => setOpen(data.open)}>
            <DialogSurface>
                <DialogBody>
                <div className="dialogBody">
                    <DialogTitle>{title}</DialogTitle>
                    <Button 
                    appearance="subtle" 
                    icon={<Dismiss24Regular />} 
                    onClick={() => setOpen(false)}
                    className="dismissButton"
                    />
                </div>
                    <DialogContent>{message}</DialogContent>
                    <DialogActions 
                     className="dialogActionContainer">
                        <Button appearance="primary" onClick={() => { onConfirm(); setOpen(false); }}
                            className="actionButton"
                        >
                            {confirmText}
                        </Button>
                        {cancelText && cancelText.trim() !== "" && (
                        <Button appearance="secondary" onClick={() => { onCancel(); setOpen(false); }}
                            className="secondaryButton"
                        >
                            {cancelText}
                        </Button>
                      )}
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};

export default ConfirmationDialog;
