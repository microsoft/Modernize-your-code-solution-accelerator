import { makeStyles, tokens } from "@fluentui/react-components";

export const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
  },
  content: {
    display: "flex",
    flex: 1,
    overflow: "hidden",
  },
  fileIcon: {
    color: tokens.colorNeutralForeground1,
    marginRight: "12px",
    flexShrink: 0,
    fontSize: "20px",
    height: "20px",
    width: "20px",
  },
  statusContainer: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginLeft: "auto",
  },
  fileName: {
    flex: 1,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    fontWeight: "600",
  },
  fileList: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    padding: "16px",
    flex: 1,
    overflow: "auto",
    paddingBottom: "70px",
  },
  panelHeader: {
    padding: "16px 20px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  fileCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    borderRadius: "4px",
    padding: "12px",
    display: "flex",
    alignItems: "center",
    cursor: "pointer",
    "&:hover": {
      backgroundColor: tokens.colorNeutralBackground3,
      border: tokens.colorBrandBackground,
    },
  },
  selectedCard: {
    border: "var(--NeutralStroke2.Rest)",
    backgroundColor: "#EBEBEB",
  },
  mainContent: {
    flex: 1,
    backgroundColor: tokens.colorNeutralBackground1,
  },
  codeCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    boxShadow: tokens.shadow4,
    overflow: "hidden",
    maxHeight: "87vh",
    overflowY: "auto",
    transition: "width 0.3s ease-in-out",
  },
  codeHeader: {
    padding: "12px 16px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  summaryContent: {
    padding: "24px",
    width: "100%", // Add this
    maxWidth: "100%", // Add this
    overflowX: "hidden", // Add this
  },
  summaryCard: {
    height: "40px",
    width: "100%",
    maxWidth: "100%", // Add this
    padding: "2px",
    backgroundColor: "#F2FBF2",
    marginBottom: "16px",
    marginLeft: "0", // Change from marginleft
    marginRight: "0",
    boxShadow: "none",
    overflowX: "hidden", // Add this
    boxSizing: "border-box", // Add this
  },
  errorSection: {
    backgroundColor: "#F8DADB",
    marginBottom: "8px",
    height: "40px",
    boxShadow: "none"
  },
  warningSection: {
    backgroundColor: tokens.colorStatusWarningBackground1,
    marginBottom: "16px",
    boxShadow: "none"
  },
  sectionHeader: {
    display: "flex",
    height: "40px",
    alignItems: "center",
    justifyContent: "space-between",
    cursor: "pointer",
    boxSizing: "border-box",
    padding: "0",
    textAlign: "left"
  },
  errorItem: {
    marginTop: "16px",
    paddingLeft: "20px",
    paddingBottom: "16px",
  },
  errorTitle: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "8px",
  },
  errorDetails: {
    marginTop: "4px",
    color: tokens.colorNeutralForeground2,
    paddingLeft: "20px",
  },
  errorSource: {
    color: tokens.colorNeutralForeground2,
    fontSize: "12px",
  },
  loadingContainer: {
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    gap: "16px",
  },
  loadingContainer_flex1: {
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    gap: "16px",
    flex: 1,
  },
  buttonContainer: {
    display: "flex",
    justifyContent: "flex-end",
    gap: "8px",
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: tokens.colorNeutralBackground2,
    borderTop: "1px solid #e5e7eb", /* Optional: adds a separator line */
    padding: "16px 20px",
    zIndex: "10",
  },
  downloadButton: {
    marginLeft: "auto",
    display: "flex",
    alignItems: "center",
    gap: "4px",
  },
  summaryHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 24px",
    transition: "width 0.3s ease-in-out" 
  },

  summaryTitle: {
    fontSize: "12px",
  },

  aiGeneratedTag: {
    color: "#6b7280", // Replacing theme.palette.text.secondary with a neutral gray
    fontSize: "0.875rem",
    backgroundColor: "#f3f4f6", // Replacing theme.palette.background.default with a light gray
    padding: "4px 8px", // Replacing theme.spacing(0.5, 1)
    borderRadius: "4px", // Replacing theme.shape.borderRadius with a standard value
  },

  noContentAvailable: {
    fontSize: "20px",
    padding: "16px",
    color: "inherit",
    textAlign: "center",
  },
  errorContent: {
    backgroundColor: "#F8DADB",
    marginBottom: "16px",
    boxShadow: "none"
  },
  warningContent: {
    backgroundColor: tokens.colorStatusWarningBackground1,
    marginBottom: "16px",
    paddingBottom: "22px",
    paddingTop: "8px",
    boxShadow: "none"
  },
  p_8:{
    padding: "8px"
  },
  p_20:{
    padding: "20px"
  },
  spinnerContainer:{
    padding: "20px",
    textAlign: "center"
  },
  aiInfoText:{
    color: tokens.colorNeutralForeground3, 
    paddingRight: "20px",
  },
  errorText:{
    color: tokens.colorStatusDangerForeground1,
  },
  errorIcon:{
    color: tokens.colorStatusDangerForeground1, 
    width: "16px", 
    height: "16px"
  },
  warningIcon:{
    color: "#B89500", 
    width: "16px", 
    height: "16px"
  },
  successIcon:{
    color: "#0B6A0B", 
    width: "16px", 
    height: "16px"
  },
  fileContent:{
    textAlign: 'center',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: '60px',
    height: '70vh',
    width: "100%",
    maxWidth: "800px",
    margin: "auto",
    transition: "width 0.3s ease-in-out",
  },
  checkMark:{
    width: '100px', 
    height: '100px', 
    marginBottom: '24px'
  },
  mb_16:{
    marginBottom: "16px"
  },
  mb_24:{
    marginBottom: "24px"
  },
  mt_16:{
    marginTop: "16px"
  },
  cursorPointer:{
    cursor: "pointer",
  },
  flex_1:{
    flex: 1
  },
  panelRight:{
    position: "fixed",
    top: "60px", // Adjust based on your header height
    right: 0,
    height: "calc(100vh - 60px)", // Ensure it does not cover the header
    width: "300px", // Set an appropriate width
    zIndex: 1050,
    background: "white",
    overflowY: "auto",
  }
});