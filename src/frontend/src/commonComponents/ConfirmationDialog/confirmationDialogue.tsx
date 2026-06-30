import React from "react";
import { Dialog, DialogSurface, DialogBody, DialogTitle, DialogContent, DialogActions } from "@fluentui/react-components";
import { Button } from "@fluentui/react-components";
import { Dismiss24Regular } from "@fluentui/react-icons";

const ConfirmationDialog = ({ open, setOpen, title, message, confirmText, cancelText, onConfirm, onCancel }) => {
    return (
        <Dialog open={open} onOpenChange={(event, data) => setOpen(data.open)}>
            <DialogSurface>
                <DialogBody>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "right" }}>
                    <DialogTitle>{title}</DialogTitle>
                    <Button 
                    appearance="subtle" 
                    icon={<Dismiss24Regular />} 
                    onClick={() => setOpen(false)}
                    style={{
                        position: "absolute",
                        top: "8px",
                        right: "8px",
                        width: "32px",
                        height: "32px",
                      }}
                    />
                </div>
                    <DialogContent>{message}</DialogContent>
                    <DialogActions 
                     style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: "8px",
                        flexWrap: "nowrap",
                      }}>
                        <Button appearance="primary" onClick={() => { onConfirm(); setOpen(false); }}
                                style={{
                                    flexGrow: 1,
                                    minWidth: "120px",
                                    maxWidth: "175px",
                                    whiteSpace: "nowrap",
                                  }}
                        >
                            {confirmText}
                        </Button>
                        {cancelText && cancelText.trim() !== "" && (
                        <Button appearance="secondary" onClick={() => { onCancel(); setOpen(false); }}
                                style={{
                                    flexGrow: 1,
                                    minWidth: "100px",
                                    maxWidth: "auto",
                                    whiteSpace: "nowrap",
                                  }}
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
